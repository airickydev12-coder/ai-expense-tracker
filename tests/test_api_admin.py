"""Tests for the admin API endpoints and authorization enforcement."""

from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.users.repository import update_user_role
from src.financial.users.role import PlatformRole

client = TestClient(app)


def _register_and_login(username: str = "alice", password: str = "correct-password") -> str:
    client.post(
        "/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )
    response = client.post("/auth/login", json={"username": username, "password": password})
    return response.json()["access_token"]


def test_admin_overview_without_authorization_header_returns_401() -> None:
    response = client.get("/admin/overview")

    assert response.status_code == 401


def test_admin_overview_rejects_plain_user() -> None:
    token = _register_and_login()

    response = client.get("/admin/overview", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_admin_overview_allows_admin() -> None:
    client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "correct-password"},
    )
    me_response = client.post(
        "/auth/login", json={"username": "alice", "password": "correct-password"}
    )
    token = me_response.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    update_user_role(me["id"], PlatformRole.ADMIN)

    response = client.get("/admin/overview", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["admin_username"] == "alice"
    assert body["admin_role"] == "admin"


def test_admin_overview_allows_super_admin() -> None:
    client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "correct-password"},
    )
    me_response = client.post(
        "/auth/login", json={"username": "alice", "password": "correct-password"}
    )
    token = me_response.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    update_user_role(me["id"], PlatformRole.SUPER_ADMIN)

    response = client.get("/admin/overview", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["admin_role"] == "super_admin"


def _register_admin(username: str = "admin", password: str = "correct-password") -> tuple[str, int]:
    """Register a user, promote to ADMIN, and return (access_token, user_id)."""
    token = _register_and_login(username, password)
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    update_user_role(me["id"], PlatformRole.ADMIN)
    return token, me["id"]


def _register_super_admin(
    username: str = "superadmin", password: str = "correct-password"
) -> tuple[str, int]:
    """Register a user, promote to SUPER_ADMIN, and return (access_token, user_id)."""
    token = _register_and_login(username, password)
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    update_user_role(me["id"], PlatformRole.SUPER_ADMIN)
    return token, me["id"]


def test_list_users_requires_admin() -> None:
    token = _register_and_login("plain")

    response = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_list_users_returns_all_accounts() -> None:
    admin_token, _ = _register_admin()
    _register_and_login("bob")

    response = client.get("/admin/users", headers={"Authorization": f"Bearer {admin_token}"})

    assert response.status_code == 200
    usernames = {user["username"] for user in response.json()}
    assert {"admin", "bob"} <= usernames


def test_get_user_returns_404_for_unknown_id() -> None:
    admin_token, _ = _register_admin()

    response = client.get("/admin/users/999999", headers={"Authorization": f"Bearer {admin_token}"})

    assert response.status_code == 404


def test_set_user_active_deactivates_target_account() -> None:
    admin_token, _ = _register_admin()
    bob_token = _register_and_login("bob")
    bob_id = client.get("/auth/me", headers={"Authorization": f"Bearer {bob_token}"}).json()["id"]

    response = client.patch(
        f"/admin/users/{bob_id}/active",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_set_user_active_rejects_self_deactivation() -> None:
    admin_token, admin_id = _register_admin()

    response = client.patch(
        f"/admin/users/{admin_id}/active",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400


def test_assign_role_requires_super_admin() -> None:
    admin_token, _ = _register_admin()
    bob_token = _register_and_login("bob")
    bob_id = client.get("/auth/me", headers={"Authorization": f"Bearer {bob_token}"}).json()["id"]

    response = client.patch(
        f"/admin/users/{bob_id}/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 403


def test_assign_role_allows_super_admin() -> None:
    super_admin_token, _ = _register_super_admin()
    bob_token = _register_and_login("bob")
    bob_id = client.get("/auth/me", headers={"Authorization": f"Bearer {bob_token}"}).json()["id"]

    response = client.patch(
        f"/admin/users/{bob_id}/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_revoke_user_sessions_ends_refresh_session() -> None:
    admin_token, _ = _register_admin()
    client.post(
        "/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "correct-password"},
    )
    bob_login_response = client.post(
        "/auth/login", json={"username": "bob", "password": "correct-password"}
    )
    bob_token = bob_login_response.json()["access_token"]
    bob_refresh_token = client.cookies.get("refresh_token")
    bob_id = client.get("/auth/me", headers={"Authorization": f"Bearer {bob_token}"}).json()["id"]

    response = client.post(
        f"/admin/users/{bob_id}/revoke-sessions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 204

    client.cookies.set("refresh_token", bob_refresh_token)
    refresh_response = client.post("/auth/refresh")
    assert refresh_response.status_code == 401
