"""Tests for the auth API endpoints."""

from datetime import datetime, timedelta, timezone

import jwt

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.config import JWT_ALGORITHM, JWT_SECRET_KEY

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
