import os
from typing import Dict, Any
import requests
from app.settings import settings

API_BASE_URL = settings.backend_api_base_url


def _auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_user(payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/auth/register"
    res = requests.post(url, json=payload, timeout=20)
    res.raise_for_status()
    return res.json()


def login_user(payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/auth/login"
    res = requests.post(url, json=payload, timeout=20)
    res.raise_for_status()
    return res.json()


def get_profile(token: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/auth/profile"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def update_profile(token: str, payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/auth/profile"
    res = requests.put(url, headers=_auth_headers(token), json=payload, timeout=20)
    res.raise_for_status()
    return res.json()


def change_password(token: str, payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/auth/change-password"
    res = requests.put(url, headers=_auth_headers(token), json=payload, timeout=20)
    res.raise_for_status()
    return res.json()


def list_users(token: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/users"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def get_user_by_id(token: str, user_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/users/{user_id}"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def get_users_by_role(token: str, role: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/users/role/{role}"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def create_user(token: str, payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/users"
    res = requests.post(url, headers=_auth_headers(token), json=payload, timeout=20)
    res.raise_for_status()
    return res.json()


def update_user(token: str, user_id: int, payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/users/{user_id}"
    res = requests.put(url, headers=_auth_headers(token), json=payload, timeout=20)
    res.raise_for_status()
    return res.json()


def delete_user(token: str, user_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/users/{user_id}"
    res = requests.delete(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def list_roles(token: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/roles"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def get_my_permissions(token: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/roles/me/permissions"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def get_role_permissions(token: str, role: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/roles/{role}"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def list_branches(token: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def get_main_branch(token: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches/main"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def get_branches_by_status(token: str, status: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches/status/{status}"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def get_branch_by_id(token: str, branch_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches/{branch_id}"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def create_branch(token: str, payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches"
    res = requests.post(url, headers=_auth_headers(token), json=payload, timeout=20)
    res.raise_for_status()
    return res.json()


def update_branch(token: str, branch_id: int, payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches/{branch_id}"
    res = requests.put(url, headers=_auth_headers(token), json=payload, timeout=20)
    res.raise_for_status()
    return res.json()


def delete_branch(token: str, branch_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches/{branch_id}"
    res = requests.delete(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def get_tenant(token: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/tenant"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def update_tenant(token: str, payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/tenant"
    res = requests.put(url, headers=_auth_headers(token), json=payload, timeout=20)
    res.raise_for_status()
    return res.json()


def upload_tenant_logo(token: str, file_path: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/tenant/logo"
    with open(file_path, "rb") as handle:
        files = {"logo": handle}
        res = requests.put(url, headers=_auth_headers(token), files=files, timeout=30)
    res.raise_for_status()
    return res.json()


def list_cars(token: str) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/cars"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def list_branch_cars(token: str, branch_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches/{branch_id}/cars"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def get_branch_car(token: str, branch_id: int, car_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches/{branch_id}/cars/{car_id}"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def create_branch_car(token: str, branch_id: int, payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches/{branch_id}/cars"
    res = requests.post(url, headers=_auth_headers(token), json=payload, timeout=20)
    res.raise_for_status()
    return res.json()


def update_branch_car(token: str, branch_id: int, car_id: int, payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches/{branch_id}/cars/{car_id}"
    res = requests.put(url, headers=_auth_headers(token), json=payload, timeout=20)
    res.raise_for_status()
    return res.json()


def delete_branch_car(token: str, branch_id: int, car_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches/{branch_id}/cars/{car_id}"
    res = requests.delete(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()



def list_car_health(token: str, branch_id: int, car_id: int) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches/{branch_id}/cars/{car_id}/health"
    res = requests.get(url, headers=_auth_headers(token), timeout=20)
    res.raise_for_status()
    return res.json()


def create_car_health(token: str, branch_id: int, car_id: int, payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/api/branches/{branch_id}/cars/{car_id}/health"
    res = requests.post(url, headers=_auth_headers(token), json=payload, timeout=20)
    res.raise_for_status()
    return res.json()
def upload_driving_license(token: str, user_id: int, file_path: str):
    url = f"{API_BASE_URL}/api/users/{user_id}/driving-license"

    filename = os.path.basename(file_path)

    with open(file_path, "rb") as f:
        files = {
            "file": (
                filename,
                f,
                "image/jpeg",  # 👈 force mimetype
            )
        }

        res = requests.put(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                # ⚠️ DO NOT set Content-Type manually
            },
            files=files,
            timeout=30,
        )

    # 🔥 TEMP DEBUG (REMOVE AFTER)
    if not res.ok:
        raise RuntimeError(f"{res.status_code} {res.text}")

    return res.json()
