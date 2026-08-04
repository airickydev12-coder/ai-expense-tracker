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
