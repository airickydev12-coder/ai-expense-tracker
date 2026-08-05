"""Tests for POST /consent/grant and /consent/revoke."""

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


def test_grant_consent_self_happy_path() -> None:
    token, user_id = _register_and_login("consenter1")

    response = client.post(
        "/consent/grant",
        json={"consent_type": "data_collection", "policy_version": "v1", "evidence": "checkbox confirmed"},
        headers=_auth(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["subject_user_id"] == user_id
    assert body["consented_by_user_id"] is None
    assert body["status"] == "granted"


def test_revoke_consent_happy_path() -> None:
    token, user_id = _register_and_login("consenter2")
    client.post(
        "/consent/grant",
        json={"consent_type": "marketing_communication", "policy_version": "v1", "evidence": "opted in"},
        headers=_auth(token),
    )

    response = client.post(
        "/consent/revoke",
        json={"consent_type": "marketing_communication", "policy_version": "v1", "evidence": "opted out"},
        headers=_auth(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "revoked"


def test_grant_consent_for_unrelated_child_returns_403() -> None:
    guardian_token, _ = _register_and_login("guardian_unrelated")
    child_token, child_id = _register_and_login("child_unrelated")

    response = client.post(
        "/consent/grant",
        json={
            "subject_user_id": child_id,
            "consent_type": "ai_coach_use",
            "policy_version": "v1",
            "evidence": "evidence",
        },
        headers=_auth(guardian_token),
    )

    assert response.status_code == 403


def test_grant_consent_requires_recent_auth() -> None:
    token, user_id = _register_and_login("consenter3")
    stale_token = _stale_access_token(user_id, "consenter3")

    response = client.post(
        "/consent/grant",
        json={"consent_type": "data_collection", "policy_version": "v1", "evidence": "evidence"},
        headers=_auth(stale_token),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "step_up_required"
