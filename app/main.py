from __future__ import annotations

import hashlib
import json
import shutil
from typing import Dict, Any, List

from fastapi import FastAPI, Header, HTTPException,UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from app.graph import build_graph, execute_action, present_tool_result, WRITE_TOOLS
from app.lc_tools import (
    tool_get_my_permissions,
    tool_get_profile,
    tool_list_branches,
    tool_upload_driving_license,
)
from app.ocr.service import analyze_driving_license_service


from .insights import build_insights
from .maintenance_insights import build_maintenance_insights
from .schemas import (
    CopilotRequest,
    CopilotResponse,
    InsightsRequest,
    InsightsResponse,
    MaintenanceInsightsRequest,
    MaintenanceInsightsResponse,
    Message,
)
from .settings import settings

# ------------------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------------------

app = FastAPI(title='RentCore Agent Server', version='0.1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()

# ------------------------------------------------------------------------------
# In-memory state (can later move to Redis)
# ------------------------------------------------------------------------------

PENDING_ACTIONS: Dict[str, Dict[str, Any]] = {}
LAST_ACTION_HASH: Dict[str, str] = {}

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _extract_token(authorization: str | None) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization.split("Bearer ", 1)[1]
    return None


def _is_confirm(message: str) -> bool:
    return message.lower().strip() in {"confirm", "تأكيد", "yes"}


def _is_cancel(message: str) -> bool:
    return message.lower().strip() in {"cancel", "إلغاء", "no"}


def _last_user_message(messages: List[Message]) -> str:
    for msg in reversed(messages):
        if msg.role == "user" and msg.content:
            return msg.content
    return ""


# ------------------------------------------------------------------------------
# Permission & scope checks
# ------------------------------------------------------------------------------

def _check_permissions(token: str | None, action: str) -> str | None:
    if not token:
        return "⛔ لا يوجد توكن صالح لهذا الطلب."

    perms = tool_get_my_permissions.invoke({"token": token})
    permissions = perms.get("data", {})

    if action in {"tool_create_user", "tool_update_user", "tool_delete_user"}:
        if not permissions.get("canManageUsers"):
            return "⛔ ليس لديك صلاحية إدارة المستخدمين."

    if action in {"tool_create_branch", "tool_update_branch", "tool_delete_branch"}:
        if not permissions.get("canManageBranches"):
            return "⛔ ليس لديك صلاحية إدارة الفروع."

    if action in {"tool_create_branch_car"}:
        if not permissions.get("canCreate"):
            return "⛔ ليس لديك صلاحية إنشاء السجلات."
    if action in {"tool_update_branch_car", "tool_update_profile", "tool_update_tenant"}:
        if not permissions.get("canUpdate"):
            return "⛔ ليس لديك صلاحية التعديل."
    if action in {"tool_delete_branch_car", "tool_delete_user", "tool_delete_branch"}:
        if not permissions.get("canDelete"):
            return "⛔ ليس لديك صلاحية الحذف."

    return None


def _check_branch_manager_scope(token: str | None, action: str, payload: Dict[str, Any]) -> str | None:
    if action not in {
        "tool_create_branch_car",
        "tool_update_branch_car",
        "tool_delete_branch_car",
    }:
        return None

    if not token:
        return "⛔ لا يوجد توكن صالح لهذا الطلب."

    profile = tool_get_profile.invoke({"token": token})
    user = profile.get("data", {}) if isinstance(profile, dict) else {}
    role = user.get("role")

    if role != "branch_manager":
        return None

    branch_id = payload.get("branch_id")
    if branch_id is None:
        return "⛔ رقم الفرع مطلوب لعمليات السيارات."

    branches = tool_list_branches.invoke({"token": token})
    branch_list = branches.get("data", []) if isinstance(branches, dict) else []
    assigned_branch = next(
        (branch for branch in branch_list if branch.get("branchManagerId") == user.get("id")),
        None,
    )

    if not assigned_branch:
        return "⛔ لا يوجد فرع معيّن لهذا المستخدم."

    if assigned_branch.get("id") != branch_id:
        return "⛔ لا يمكنك إدارة سيارات خارج الفرع المعيّن لك."

    return None


# ------------------------------------------------------------------------------
# Health
# ------------------------------------------------------------------------------

@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "openai_configured": bool(settings.openai_api_key),
        "model": settings.openai_model,
    }


# ------------------------------------------------------------------------------
# Chat (MAIN ENTRY)
# ------------------------------------------------------------------------------

@app.post("/chat", response_model=CopilotResponse)
def chat(req: CopilotRequest, authorization: str = Header(None)) -> CopilotResponse:
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages array is required")

    token = _extract_token(authorization)
    last_message = req.messages[-1].content

    # -------------------------
    # Cancel flow
    # -------------------------
    if _is_cancel(last_message):
        if token in PENDING_ACTIONS:
            PENDING_ACTIONS.pop(token, None)
        return CopilotResponse(
            response="تم إلغاء العملية ✅",
            suggestions=["ابدأ من جديد"],
            metadata={"source": "agent"},
        )

    # -------------------------
    # Confirm flow
    # -------------------------
    if _is_confirm(last_message) and token in PENDING_ACTIONS:
        pending = PENDING_ACTIONS.pop(token)
        action = pending["action"]
        payload = pending["payload"]

        perm_error = _check_permissions(token, action)
        if perm_error:
            return CopilotResponse(
                response=perm_error,
                suggestions=["عرض الصلاحيات"],
                metadata={"source": "agent"},
            )

        branch_scope_error = _check_branch_manager_scope(token, action, payload)
        if branch_scope_error:
            return CopilotResponse(
                response=branch_scope_error,
                suggestions=["عرض الفروع"],
                metadata={"source": "agent"},
            )

        payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        if LAST_ACTION_HASH.get(token) == payload_hash:
            return CopilotResponse(
                response="تم تنفيذ هذه العملية مسبقًا ✅",
                suggestions=["عرض النتائج"],
                metadata={"source": "agent"},
            )

        try:
            result = execute_action(action, token, payload)
        except Exception as exc:  # noqa: BLE001
            return CopilotResponse(
                response=f"⚠️ حدث خطأ أثناء التنفيذ: {exc}",
                suggestions=["حاول مرة أخرى"],
                metadata={"source": "agent"},
            )

        LAST_ACTION_HASH[token] = payload_hash
        formatted_result = present_tool_result(
            result,
            req.context.user if req.context else None,
            action,
        )
        return CopilotResponse(
            response=f"تم تنفيذ العملية بنجاح ✅\n{formatted_result}",
            suggestions=["طلب آخر"],
            metadata={"source": "agent"},
        )

    result = graph.invoke(
        {
            "messages": req.messages,
            "user": req.context.user if req.context else None,
            "token": token,
        }
    )

    if result.get("pending_action") and token:
        if result["pending_action"] in WRITE_TOOLS:
            PENDING_ACTIONS[token] = {
                "action": result["pending_action"],
                "payload": result.get("pending_payload", {}),
            }

        return CopilotResponse(
            response=result.get("response_text", "هل تريد تأكيد التنفيذ؟"),
            suggestions=["تأكيد", "إلغاء"],
            metadata={"source": "agent"},
        )

    return CopilotResponse(
        response=result.get("response_text", ""),
        suggestions=["متابعة"],
        metadata={"source": "agent"},
    )


# ------------------------------------------------------------------------------
# Insights
# ------------------------------------------------------------------------------

@app.post("/insights", response_model=InsightsResponse)
def insights(payload: InsightsRequest) -> InsightsResponse:
    if payload.type == "multi-series" and not payload.valueKeys:
        raise HTTPException(
            status_code=400,
            detail="valueKeys is required for multi-series",
        )

    if payload.type in {"series", "pie"} and not payload.valueKey:
        raise HTTPException(
            status_code=400,
            detail="valueKey is required",
        )

    insights_items = build_insights(payload)
    return InsightsResponse(
        insights=insights_items,
        source="python",
    )

# ------------------------------------------------------------------------------
# Maintenance insights (risk + ROI + root cause)
# ------------------------------------------------------------------------------


@app.post("/maintenance-insights", response_model=MaintenanceInsightsResponse)
def maintenance_insights(payload: MaintenanceInsightsRequest) -> MaintenanceInsightsResponse:
    return build_maintenance_insights(payload)

@app.post("/analysis-license")
def analysis_license(
    user_id: int,
    file: UploadFile = File(...),
    authorization: str = Header(None),
):
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    upload = tool_upload_driving_license.invoke({
        "token": token,
        "user_id": user_id,
        "file_path": temp_path,
    })

    image_url = upload["data"]["driving_license_url"]

    return analyze_driving_license_service(
        image_url=image_url,
        country=None,
        car=None,
    )

@app.post("/analyze-driving-license")
def analyze_driving_license(payload: dict):
    return analyze_driving_license_service(
        image_url=payload["image_url"],
        country=payload.get("country"),
        car=payload.get("car"),
    )