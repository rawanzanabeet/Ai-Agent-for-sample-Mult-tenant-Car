from langchain_core.tools import tool
from app import tools
from app.ocr.service import analyze_driving_license_service


@tool
def tool_register_user(payload: dict):
    """Register a user or business."""
    return tools.register_user(payload)


@tool
def tool_login_user(payload: dict):
    """Login user."""
    return tools.login_user(payload)


@tool
def tool_get_profile(token: str):
    """Get current user profile."""
    return tools.get_profile(token)


@tool
def tool_update_profile(token: str, payload: dict):
    """Update current user profile."""
    return tools.update_profile(token, payload)


@tool
def tool_change_password(token: str, payload: dict):
    """Change current user password."""
    return tools.change_password(token, payload)


@tool
def tool_list_users(token: str):
    """List users."""
    return tools.list_users(token)


@tool
def tool_get_user_by_id(token: str, user_id: int):
    """Get user by id."""
    return tools.get_user_by_id(token, user_id)


@tool
def tool_get_users_by_role(token: str, role: str):
    """Get users by role."""
    return tools.get_users_by_role(token, role)


@tool
def tool_create_user(token: str, payload: dict):
    """Create user."""
    return tools.create_user(token, payload)


@tool
def tool_update_user(token: str, user_id: int, payload: dict):
    """Update user."""
    return tools.update_user(token, user_id, payload)


@tool
def tool_delete_user(token: str, user_id: int):
    """Delete user."""
    return tools.delete_user(token, user_id)


@tool
def tool_list_roles(token: str):
    """List roles."""
    return tools.list_roles(token)


@tool
def tool_get_my_permissions(token: str):
    """Get current user permissions."""
    return tools.get_my_permissions(token)


@tool
def tool_get_role_permissions(token: str, role: str):
    """Get role permissions."""
    return tools.get_role_permissions(token, role)


@tool
def tool_list_branches(token: str):
    """List branches."""
    return tools.list_branches(token)


@tool
def tool_get_main_branch(token: str):
    """Get main branch."""
    return tools.get_main_branch(token)


@tool
def tool_get_branches_by_status(token: str, status: str):
    """Get branches by status."""
    return tools.get_branches_by_status(token, status)


@tool
def tool_get_branch_by_id(token: str, branch_id: int):
    """Get branch by id."""
    return tools.get_branch_by_id(token, branch_id)


@tool
def tool_create_branch(token: str, payload: dict):
    """Create branch."""
    return tools.create_branch(token, payload)


@tool
def tool_update_branch(token: str, branch_id: int, payload: dict):
    """Update branch."""
    return tools.update_branch(token, branch_id, payload)


@tool
def tool_delete_branch(token: str, branch_id: int):
    """Delete branch."""
    return tools.delete_branch(token, branch_id)


@tool
def tool_get_tenant(token: str):
    """Get tenant info."""
    return tools.get_tenant(token)


@tool
def tool_update_tenant(token: str, payload: dict):
    """Update tenant info."""
    return tools.update_tenant(token, payload)


@tool
def tool_upload_tenant_logo(token: str, file_path: str):
    """Upload tenant logo."""
    return tools.upload_tenant_logo(token, file_path)


@tool
def tool_list_cars(token: str):
    """List cars (tenant)."""
    return tools.list_cars(token)


@tool
def tool_list_branch_cars(token: str, branch_id: int):
    """List cars for branch."""
    return tools.list_branch_cars(token, branch_id)


@tool
def tool_get_branch_car(token: str, branch_id: int, car_id: int):
    """Get car in branch."""
    return tools.get_branch_car(token, branch_id, car_id)


@tool
def tool_create_branch_car(token: str, branch_id: int, payload: dict):
    """Create car in branch."""
    return tools.create_branch_car(token, branch_id, payload)


@tool
def tool_update_branch_car(token: str, branch_id: int, car_id: int, payload: dict):
    """Update car in branch."""
    return tools.update_branch_car(token, branch_id, car_id, payload)


@tool
def tool_delete_branch_car(token: str, branch_id: int, car_id: int):
    """Delete car in branch."""
    return tools.delete_branch_car(token, branch_id, car_id)


@tool
def tool_list_car_health(token: str, branch_id: int, car_id: int):
    """List car health records for a car in a branch."""
    return tools.list_car_health(token, branch_id, car_id)


@tool
def tool_create_car_health(token: str, branch_id: int, car_id: int, payload: dict):
    """Create a car health record for a car in a branch."""
    return tools.create_car_health(token, branch_id, car_id, payload)

@tool
def tool_upload_driving_license(token: str, user_id: int, file_path: str):
    """
    Upload a driving license image for a user and return the public image URL.
    """
    return tools.upload_driving_license(token, user_id, file_path)


@tool
def tool_analyze_driving_license(payload: dict):
    """
    Analyze driving license using local OCR and return validation & risk.
    """
    return analyze_driving_license_service(
        image_url=payload["image_url"],
        country=payload.get("country"),
        car=payload.get("car"),
    )