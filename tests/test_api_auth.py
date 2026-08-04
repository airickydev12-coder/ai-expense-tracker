"""Tests for the auth API endpoints."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from src.financial.users import service as user_service

client = TestClient(app)


def _register(username: str = "alice", password: str = "correct-password"):
    return client.post(
        "/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )


def test_register_success() -> None:
    response = _register()

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_username_returns_400() -> None:
    _register()

    response = _register()

    assert response.status_code == 400


def test_register_weak_password_returns_422() -> None:
    response = client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "short"},
    )

    # Pydantic schema validation (min_length=8) fails before our domain
    # ValidationError handler ever runs, so this is FastAPI's own 422 —
    # a distinct code path from the 400 duplicate-username case above.
    assert response.status_code == 422


def test_login_success() -> None:
    _register()

    response = client.post("/auth/login", json={"username": "alice", "password": "correct-password"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]


def test_login_wrong_password_returns_401() -> None:
    _register()

    wrong_password_response = client.post(
        "/auth/login", json={"username": "alice", "password": "wrong-password"}
    )
    nonexistent_user_response = client.post(
        "/auth/login", json={"username": "nobody", "password": "correct-password"}
    )

    assert wrong_password_response.status_code == 401
    assert nonexistent_user_response.status_code == 401
    # Same message in both cases: don't leak whether the username exists.
    assert wrong_password_response.json()["detail"] == nonexistent_user_response.json()["detail"]


def test_me_with_valid_token() -> None:
    _register()
    token = client.post(
        "/auth/login", json={"username": "alice", "password": "correct-password"}
    ).json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_me_without_authorization_header_returns_401() -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_with_malformed_token_returns_401() -> None:
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_update_profile_success() -> None:
    _register()
    token = client.post(
        "/auth/login", json={"username": "alice", "password": "correct-password"}
    ).json()["access_token"]

    response = client.patch(
        "/auth/me",
        json={"username": "alice2"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "alice2"


def test_update_profile_requires_at_least_one_field() -> None:
    _register()
    token = client.post(
        "/auth/login", json={"username": "alice", "password": "correct-password"}
    ).json()["access_token"]

    response = client.patch(
        "/auth/me",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


def test_update_profile_duplicate_username_returns_400() -> None:
    _register("alice")
    _register("bob")
    token = client.post(
        "/auth/login", json={"username": "bob", "password": "correct-password"}
    ).json()["access_token"]

    response = client.patch(
        "/auth/me",
        json={"username": "alice"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


def test_update_profile_without_authorization_header_returns_401() -> None:
    response = client.patch("/auth/me", json={"username": "alice2"})

    assert response.status_code == 401


def test_change_password_success() -> None:
    _register()
    token = client.post(
        "/auth/login", json={"username": "alice", "password": "correct-password"}
    ).json()["access_token"]

    response = client.post(
        "/auth/change-password",
        json={"current_password": "correct-password", "new_password": "new-password"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204

    new_login = client.post("/auth/login", json={"username": "alice", "password": "new-password"})
    assert new_login.status_code == 200


def test_change_password_rejects_wrong_current_password() -> None:
    _register()
    token = client.post(
        "/auth/login", json={"username": "alice", "password": "correct-password"}
    ).json()["access_token"]

    response = client.post(
        "/auth/change-password",
        json={"current_password": "wrong-password", "new_password": "new-password"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_change_password_rejects_weak_new_password() -> None:
    _register()
    token = client.post(
        "/auth/login", json={"username": "alice", "password": "correct-password"}
    ).json()["access_token"]

    response = client.post(
        "/auth/change-password",
        json={"current_password": "correct-password", "new_password": "short"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_change_password_without_authorization_header_returns_401() -> None:
    response = client.post(
        "/auth/change-password",
        json={"current_password": "correct-password", "new_password": "new-password"},
    )

    assert response.status_code == 401


def test_forgot_password_returns_202_for_known_email(monkeypatch: pytest.MonkeyPatch) -> None:
    _register()

    sent: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: sent.update(body=body),
    )

    response = client.post("/auth/forgot-password", json={"email": "alice@example.com"})

    assert response.status_code == 202
    assert "reset-password?token=" in sent["body"]


def test_forgot_password_returns_202_for_unknown_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: pytest.fail("Should not send for an unknown email"),
    )

    response = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})

    # Same 202 either way -- don't leak whether the email is registered.
    assert response.status_code == 202


def test_reset_password_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _register()

    sent: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: sent.update(body=body),
    )
    client.post("/auth/forgot-password", json={"email": "alice@example.com"})
    token = sent["body"].split("reset-password?token=")[1].split("\n")[0]

    response = client.post(
        "/auth/reset-password", json={"token": token, "new_password": "new-password"}
    )

    assert response.status_code == 204

    new_login = client.post("/auth/login", json={"username": "alice", "password": "new-password"})
    assert new_login.status_code == 200


def test_reset_password_rejects_invalid_token() -> None:
    response = client.post(
        "/auth/reset-password", json={"token": "not-a-real-token", "new_password": "new-password"}
    )

    assert response.status_code == 400


def test_refresh_success() -> None:
    _register()
    login_response = client.post(
        "/auth/login", json={"username": "alice", "password": "correct-password"}
    ).json()

    response = client.post(
        "/auth/refresh", json={"refresh_token": login_response["refresh_token"]}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["refresh_token"] != login_response["refresh_token"]

    # The new access token is valid.
    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me_response.status_code == 200


def test_refresh_rejects_already_rotated_token() -> None:
    _register()
    login_response = client.post(
        "/auth/login", json={"username": "alice", "password": "correct-password"}
    ).json()

    client.post("/auth/refresh", json={"refresh_token": login_response["refresh_token"]})
    reused_response = client.post(
        "/auth/refresh", json={"refresh_token": login_response["refresh_token"]}
    )

    assert reused_response.status_code == 401


def test_refresh_rejects_unknown_token() -> None:
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-real-refresh-token"})

    assert response.status_code == 401


def test_login_locks_out_after_max_failed_attempts() -> None:
    from src.core.config import LOGIN_LOCKOUT_MAX_ATTEMPTS

    _register()

    for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
        response = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
        assert response.status_code == 401

    locked_out_response = client.post(
        "/auth/login", json={"username": "alice", "password": "correct-password"}
    )

    assert locked_out_response.status_code == 429


def test_me_with_expired_token_returns_401() -> None:
    now = datetime.now(timezone.utc)
    expired_token = jwt.encode(
        {
            "sub": "1",
            "username": "alice",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401
