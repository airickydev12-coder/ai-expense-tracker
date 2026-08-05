"""Tests for POST /account/request-adult-transition."""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from src.api.main import app
from src.core.config import JWT_ALGORITHM, JWT_SECRET_KEY, STEP_UP_MAX_AGE_MINUTES

client = TestClient(app)


def _stale_access_token(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user_id),
            "username": username,
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "auth_time": int((now - timedelta(minutes=STEP_UP_MAX_AGE_MINUTES + 1)).timestamp()),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def _register_and_login(username: str = "alice", password: str = "correct-password") -> tuple[str, int]:
    client.post(
        "/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )
    token = client.post("/auth/login", json={"username": username, "password": password}).json()[
        "access_token"
    ]
    user_id = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["id"]
    return token, user_id


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_request_adult_transition_happy_path() -> None:
    guardian_token, _ = _register_and_login("guardian_transition")
    household_id = client.post(
        "/households", json={"name": "Smith Family"}, headers=_auth(guardian_token)
    ).json()["id"]
    client.post(
        f"/households/{household_id}/children",
        json={
            "username": "transitioning_teen",
            "email": "transitioning_teen@example.com",
            "password": "correct-password",
            "age_band": "14-17",
            "policy_version": "v1",
            "evidence": "evidence",
        },
        headers=_auth(guardian_token),
    )
    child_token = client.post(
        "/auth/login",
        json={"username": "transitioning_teen", "password": "correct-password"},
    ).json()["access_token"]

    response = client.post("/account/request-adult-transition", headers=_auth(child_token))

    assert response.status_code == 200
    assert response.json()["account_type"] == "adult"

    guardian_children = client.get("/guardian/children", headers=_auth(guardian_token))
    assert guardian_children.json() == []


def test_request_adult_transition_rejects_already_adult() -> None:
    token, _ = _register_and_login("already_adult")

    response = client.post("/account/request-adult-transition", headers=_auth(token))

    assert response.status_code == 400


def test_request_adult_transition_requires_recent_auth() -> None:
    guardian_token, _ = _register_and_login("guardian_transition2")
    household_id = client.post(
        "/households", json={"name": "Smith Family"}, headers=_auth(guardian_token)
    ).json()["id"]
    child_response = client.post(
        f"/households/{household_id}/children",
        json={
            "username": "teen2",
            "email": "teen2@example.com",
            "password": "correct-password",
            "age_band": "14-17",
            "policy_version": "v1",
            "evidence": "evidence",
        },
        headers=_auth(guardian_token),
    )
    child_id = child_response.json()["child"]["id"]
    stale_token = _stale_access_token(child_id, "teen2")

    response = client.post("/account/request-adult-transition", headers=_auth(stale_token))

    assert response.status_code == 403
    assert response.json()["code"] == "step_up_required"
