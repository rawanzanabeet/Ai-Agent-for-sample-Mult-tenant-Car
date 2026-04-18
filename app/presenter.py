from __future__ import annotations

from typing import Any, Optional

from app.schemas import ContextUser

MAX_LIST_ITEMS = 5


def present_tool_result(
    tool_name: str | None,
    data: Any,
    user: Optional[ContextUser],
    locale: str,
) -> str:
    role = (user.role if user else None) or "unknown"
    normalized_locale = _normalize_locale(locale)
    error_message = _extract_error(data, normalized_locale)
    if error_message:
        return error_message

    payload = _unwrap_data(data)
    if payload is None or payload == [] or payload == {}:
        return _empty_message(normalized_locale)

    if isinstance(payload, list):
        return _present_list(tool_name, payload, role, normalized_locale)

    return _present_details(tool_name, payload, role, normalized_locale)


def _normalize_locale(locale: str | None) -> str:
    if locale and locale.lower().startswith("en"):
        return "en"
    return "ar"


def _unwrap_data(data: Any) -> Any:
    if isinstance(data, dict) and "data" in data and len(data) <= 3:
        return data.get("data")
    return data


def _extract_error(data: Any, locale: str) -> str | None:
    if not isinstance(data, dict):
        return None

    if data.get("error"):
        return _format_error(data.get("error"), locale)

    if data.get("status") is False or data.get("success") is False:
        return _format_error(data.get("message") or data.get("detail"), locale)

    return None


def _format_error(message: Any, locale: str) -> str:
    text = str(message) if message else _default_error(locale)
    if locale == "en":
        return f"⚠️ {text}"
    return f"⚠️ {text}"


def _default_error(locale: str) -> str:
    if locale == "en":
        return "Something went wrong while fetching the data."
    return "حدث خطأ أثناء جلب البيانات."


def _empty_message(locale: str) -> str:
    if locale == "en":
        return "No results found. Would you like to try a different query?"
    return "ما في نتائج مطابقة. تحب نجرب استعلام مختلف؟"


def _present_list(tool_name: str | None, items: list[Any], role: str, locale: str) -> str:
    count = len(items)
    label = _label_for_tool(tool_name, locale, count)
    header = _list_header(count, label, locale)
    preview = items[:MAX_LIST_ITEMS]
    lines = [header, ""]
    for item in preview:
        lines.append(f"- {_format_item(tool_name, item, role, locale)}")

    remaining = count - len(preview)
    if remaining > 0:
        lines.append(_remaining_line(remaining, locale))

    suggestion = _list_suggestion(tool_name, locale)
    if suggestion:
        lines.extend(["", suggestion])

    return "\n".join(line for line in lines if line)


def _present_details(tool_name: str | None, item: Any, role: str, locale: str) -> str:
    formatted = _format_item(tool_name, item, role, locale)
    suggestion = _details_suggestion(tool_name, locale)
    if suggestion:
        return f"{formatted}\n\n{suggestion}"
    return formatted


def _list_header(count: int, label: str, locale: str) -> str:
    if locale == "en":
        return f"You have {count} {label}:"
    return f"عندك {count} {label}:"


def _remaining_line(remaining: int, locale: str) -> str:
    if locale == "en":
        return f"… and {remaining} more"
    return f"… و {remaining} أخرى"


def _label_for_tool(tool_name: str | None, locale: str, count: int) -> str:
    plural = "s" if count != 1 else ""
    if tool_name == "tool_list_branches":
        return "branches" if locale == "en" else "فروع"
    if tool_name == "tool_list_users" or tool_name == "tool_get_users_by_role":
        return "users" if locale == "en" else "مستخدمين"
    if tool_name in {"tool_list_cars", "tool_list_branch_cars"}:
        return "cars" if locale == "en" else "سيارات"
    if tool_name == "tool_list_roles":
        return "roles" if locale == "en" else "أدوار"
    return f"item{plural}" if locale == "en" else "عناصر"


def _format_item(tool_name: str | None, item: Any, role: str, locale: str) -> str:
    if isinstance(item, dict):
        if tool_name and "branch" in tool_name:
            return _format_branch(item, role, locale)
        if tool_name and "user" in tool_name:
            return _format_user(item, locale)
        if tool_name and "car" in tool_name:
            return _format_car(item, locale)
        if tool_name and "role" in tool_name:
            return _format_role(item, locale)
    return _fallback_item(item, locale)


def _format_branch(item: dict, role: str, locale: str) -> str:
    name = item.get("name") or item.get("branchName") or item.get("title") or _unknown(locale)
    status = item.get("status") or item.get("branchStatus")
    city = item.get("city")
    cars_count = item.get("carsCount") or item.get("cars_count") or item.get("cars")
    performance = item.get("performance") or item.get("rating")

    parts: list[str] = [name]
    if status:
        parts.append(str(status))
    if city:
        parts.append(str(city))

    if role in {"owner", "admin"}:
        if cars_count is not None:
            label = "cars" if locale == "en" else "سيارات"
            parts.append(f"{cars_count} {label}")
        if performance is not None:
            label = "performance" if locale == "en" else "الأداء"
            parts.append(f"{label}: {performance}")

    return " — ".join(str(part) for part in parts if part)


def _format_user(item: dict, locale: str) -> str:
    name_parts = [item.get("firstName"), item.get("lastName")]
    name = " ".join(part for part in name_parts if part) or item.get("name") or _unknown(locale)
    role = item.get("role")
    email = item.get("email")

    parts = [name]
    if role:
        parts.append(str(role))
    if email:
        parts.append(str(email))
    return " — ".join(parts)


def _format_car(item: dict, locale: str) -> str:
    name = item.get("name") or item.get("model") or item.get("carModel") or _unknown(locale)
    plate = item.get("plateNumber") or item.get("plate")
    status = item.get("status")
    parts = [name]
    if plate:
        parts.append(str(plate))
    if status:
        parts.append(str(status))
    return " — ".join(parts)


def _format_role(item: dict, locale: str) -> str:
    name = item.get("name") or item.get("role") or _unknown(locale)
    description = item.get("description")
    parts = [name]
    if description:
        parts.append(str(description))
    return " — ".join(parts)


def _fallback_item(item: Any, locale: str) -> str:
    if item is None:
        return _unknown(locale)
    if isinstance(item, (str, int, float)):
        return str(item)
    return _unknown(locale)


def _unknown(locale: str) -> str:
    return "غير معروف" if locale == "ar" else "Unknown"


def _list_suggestion(tool_name: str | None, locale: str) -> str | None:
    if not tool_name:
        return None
    if "branch" in tool_name:
        if locale == "en":
            return "Would you like details for a specific branch?"
        return "بدك تفاصيل فرع معيّن؟"
    if "car" in tool_name:
        if locale == "en":
            return "Want to view details for a specific car?"
        return "تحب تفاصيل سيارة معيّنة؟"
    if "user" in tool_name:
        if locale == "en":
            return "Need details for a specific user?"
        return "بدك تفاصيل مستخدم معيّن؟"
    return None


def _details_suggestion(tool_name: str | None, locale: str) -> str | None:
    if not tool_name:
        return None
    if "branch" in tool_name:
        if locale == "en":
            return "Would you like to update the branch status?"
        return "بدك نعدّل حالة الفرع؟"
    if "car" in tool_name:
        if locale == "en":
            return "Want to update this car or list cars in the branch?"
        return "تحب نعدّل السيارة أو نعرض سيارات الفرع؟"
    return None