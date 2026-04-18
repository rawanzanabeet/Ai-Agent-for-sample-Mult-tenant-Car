from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.schemas import ContextUser, Message
from app.settings import settings
from app import lc_tools


# ------------------------------------------------------------------------------
# Graph State
# ------------------------------------------------------------------------------

class GraphState(TypedDict, total=False):
    messages: List[Message]
    user: Optional[ContextUser]
    token: Optional[str]

    tool_name: Optional[str]
    tool_result: Optional[Any]

    response_text: Optional[str]
    pending_action: Optional[str]
    pending_payload: Optional[Dict[str, Any]]


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

WRITE_TOOLS = {
    "tool_create_user",
    "tool_update_user",
    "tool_delete_user",
    "tool_create_branch",
    "tool_update_branch",
    "tool_delete_branch",
    "tool_create_branch_car",
    "tool_update_branch_car",
    "tool_delete_branch_car",
    "tool_create_car_health",
    "tool_update_tenant",
    "tool_update_profile",
    "tool_change_password",
    "tool_upload_tenant_logo",
}

MISSING_TOKEN_MESSAGE = (
    "⛔ لا يوجد توكن صالح لهذا الطلب. الرجاء تسجيل الدخول وإرسال Authorization: Bearer <token>."
)

TOOL_HANDLERS = {
    "tool_get_profile": lc_tools.tool_get_profile,
    "tool_update_profile": lc_tools.tool_update_profile,
    "tool_change_password": lc_tools.tool_change_password,
    "tool_list_users": lc_tools.tool_list_users,
    "tool_get_user_by_id": lc_tools.tool_get_user_by_id,
    "tool_get_users_by_role": lc_tools.tool_get_users_by_role,
    "tool_create_user": lc_tools.tool_create_user,
    "tool_update_user": lc_tools.tool_update_user,
    "tool_delete_user": lc_tools.tool_delete_user,
    "tool_list_roles": lc_tools.tool_list_roles,
    "tool_get_my_permissions": lc_tools.tool_get_my_permissions,
    "tool_get_role_permissions": lc_tools.tool_get_role_permissions,
    "tool_list_branches": lc_tools.tool_list_branches,
    "tool_get_main_branch": lc_tools.tool_get_main_branch,
    "tool_get_branches_by_status": lc_tools.tool_get_branches_by_status,
    "tool_get_branch_by_id": lc_tools.tool_get_branch_by_id,
    "tool_create_branch": lc_tools.tool_create_branch,
    "tool_update_branch": lc_tools.tool_update_branch,
    "tool_delete_branch": lc_tools.tool_delete_branch,
    "tool_get_tenant": lc_tools.tool_get_tenant,
    "tool_update_tenant": lc_tools.tool_update_tenant,
    "tool_upload_tenant_logo": lc_tools.tool_upload_tenant_logo,
    "tool_list_cars": lc_tools.tool_list_cars,
    "tool_list_branch_cars": lc_tools.tool_list_branch_cars,
    "tool_get_branch_car": lc_tools.tool_get_branch_car,
    "tool_create_branch_car": lc_tools.tool_create_branch_car,
    "tool_update_branch_car": lc_tools.tool_update_branch_car,
    "tool_delete_branch_car": lc_tools.tool_delete_branch_car,
    "tool_list_car_health": lc_tools.tool_list_car_health,
    "tool_create_car_health": lc_tools.tool_create_car_health,
}


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def to_markdown(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return f"```json\n{json.dumps(value, ensure_ascii=False, indent=2)}\n```"
    return str(value)


def get_last_user_message(messages: List[Message]) -> str:
    for msg in reversed(messages):
        if msg.role == "user" and msg.content:
            return msg.content
    return ""


# ------------------------------------------------------------------------------
# System Prompt (Main LLM)
# ------------------------------------------------------------------------------

def build_system_prompt(user: Optional[ContextUser]) -> str:
    prompt = "You are RentCore AI. Be concise unless asked for detail."

    if user:
        prompt += (
            f" User: {user.firstName or ''} {user.lastName or ''}."
            f" Role: {user.role or 'unknown'}."
            f" Tenant: {user.tenant or 'unknown'}."
        )

    prompt += " If a tool is needed, call it with minimal required fields."
    return prompt


# ------------------------------------------------------------------------------
# Presenter Prompt (GLOBAL)
# ------------------------------------------------------------------------------

def build_presenter_prompt(
    user: Optional[ContextUser],
    tool_name: Optional[str],
    user_message: str,
) -> str:
    return f"""
You are a global AI Presenter for RentCore.

Your role:
- Convert raw tool results into human, conversational responses.
- Never sound like a database or report.
- Never dump all details unless the user explicitly asked for them.

Conversation rules:
1. If the user question is GENERAL:
   - Start with a short summary.
   - Mention counts and high-level status.
   - Show only key identifiers.
   - Ask what they want next.

2. If the user question is DETAILED:
   - Provide full relevant details.

Context:
- Tool name: {tool_name}
- User role: {user.role if user else "unknown"}
- User message: "{user_message}"

Output language:
- Match the user's language automatically.

DO NOT:
- Return raw JSON
- Repeat backend field names
"""


# ------------------------------------------------------------------------------
# Presenter Execution
# ------------------------------------------------------------------------------

def present_tool_result(
    value: Any,
    user: Optional[ContextUser],
    tool_name: Optional[str],
    last_user_message: str,
) -> str:
    if not settings.openai_api_key:
        return to_markdown(value)

    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=0.2,
    )

    payload = json.dumps(value, ensure_ascii=False, indent=2)

    response = llm.invoke(
        [
            {
                "role": "system",
                "content": build_presenter_prompt(
                    user,
                    tool_name,
                    last_user_message,
                ),
            },
            {
                "role": "user",
                "content": f"Tool result:\n{payload}",
            },
        ]
    )

    return response.content


# ------------------------------------------------------------------------------
# Intent Router
# ------------------------------------------------------------------------------

def intent_router_node(state: GraphState) -> dict:
    text = state["messages"][-1].content.lower()

    if any(k in text for k in ["أنشئ", "احذف", "تعديل", "update", "delete", "create"]):
        return {"intent": "write"}

    if any(k in text for k in ["عرض", "list", "show", "get", "استعلام"]):
        return {"intent": "read"}

    return {"intent": "chat"}


# ------------------------------------------------------------------------------
# Tool Execution
# ------------------------------------------------------------------------------

def execute_action(action: str, token: Optional[str], payload: Dict[str, Any]) -> Any:
    handler = TOOL_HANDLERS.get(action)
    if not handler:
        raise ValueError(f"Unknown tool: {action}")

    if "token" in handler.args:
        if not token:
            raise ValueError(MISSING_TOKEN_MESSAGE)

        payload = {k: v for k, v in payload.items() if k != "token"}
        return handler.invoke({"token": token, **payload})

    return handler.invoke(payload)


# ------------------------------------------------------------------------------
# Confirmation Message
# ------------------------------------------------------------------------------

def build_confirmation_message(action: str, payload: Dict[str, Any]) -> str:
    if action == "tool_delete_branch_car":
        return f"سيتم حذف السيارة. هل تؤكد؟"
    if action == "tool_create_car_health":
        return "سيتم إنشاء سجل صحة جديد للسيارة. هل تؤكد؟"
    if action == "tool_delete_user":
        return f"سيتم حذف المستخدم. هل تؤكد؟"
    if action == "tool_delete_branch":
        return f"سيتم حذف الفرع. هل تؤكد؟"
    return "عملية كتابة تحتاج تأكيد. هل تؤكد؟"


# ------------------------------------------------------------------------------
# Main LLM Node
# ------------------------------------------------------------------------------

def llm_node(state: GraphState) -> dict:
    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=0.5,
    ).bind_tools(list(TOOL_HANDLERS.values()))

    system_prompt = build_system_prompt(state.get("user"))
    chat_messages = [{"role": "system", "content": system_prompt}]

    for msg in state["messages"]:
        chat_messages.append({"role": msg.role, "content": msg.content})

    response = llm.invoke(chat_messages)

    if response.tool_calls:
        tool_call = response.tool_calls[0]
        action = tool_call["name"]
        payload = tool_call["args"]

        handler = TOOL_HANDLERS.get(action)
        if handler and "token" in handler.args and not state.get("token"):
            return {"response_text": MISSING_TOKEN_MESSAGE}

        if action in WRITE_TOOLS:
            return {
                "pending_action": action,
                "pending_payload": payload,
                "response_text": build_confirmation_message(action, payload),
            }

        result = execute_action(action, state.get("token"), payload)
        return {
            "tool_name": action,
            "tool_result": result,
        }

    return {"response_text": response.content}


# ------------------------------------------------------------------------------
# Formatter Node
# ------------------------------------------------------------------------------

def format_node(state: GraphState) -> dict:
    if state.get("response_text"):
        return {"response_text": state["response_text"]}

    if state.get("tool_result"):
        last_user_message = get_last_user_message(state["messages"])
        return {
            "response_text": present_tool_result(
                state["tool_result"],
                state.get("user"),
                state.get("tool_name"),
                last_user_message,
            )
        }

    return {"response_text": "لا توجد نتيجة متاحة."}


# ------------------------------------------------------------------------------
# Build Graph
# ------------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("router", intent_router_node)
    graph.add_node("llm", llm_node)
    graph.add_node("format", format_node)

    graph.set_entry_point("router")
    graph.add_edge("router", "llm")
    graph.add_edge("llm", "format")
    graph.add_edge("format", END)

    return graph.compile()
