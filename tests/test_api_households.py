"""Tests for the household API endpoints."""

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


def test_create_household_makes_actor_the_owner() -> None:
    token, user_id = _register_and_login("owner1")

    response = client.post("/households", json={"name": "Smith Family"}, headers=_auth(token))

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Smith Family"
    assert len(body["members"]) == 1
    assert body["members"][0]["user_id"] == user_id
    assert body["members"][0]["household_role"] == "owner"


def test_get_household_returns_404_for_non_member() -> None:
    owner_token, _ = _register_and_login("owner2")
    outsider_token, _ = _register_and_login("outsider2")
    household_id = client.post(
        "/households", json={"name": "Smith Family"}, headers=_auth(owner_token)
    ).json()["id"]

    response = client.get(f"/households/{household_id}", headers=_auth(outsider_token))

    assert response.status_code == 404


def test_add_member_as_non_owner_returns_403() -> None:
    owner_token, _ = _register_and_login("owner3")
    member_token, member_id = _register_and_login("member3")
    outsider_token, outsider_id = _register_and_login("outsider3")
    household_id = client.post(
        "/households", json={"name": "Smith Family"}, headers=_auth(owner_token)
    ).json()["id"]
    client.post(
        f"/households/{household_id}/members",
        json={"user_id": member_id, "household_role": "adult_member"},
        headers=_auth(owner_token),
    )

    response = client.post(
        f"/households/{household_id}/members",
        json={"user_id": outsider_id, "household_role": "adult_member"},
        headers=_auth(member_token),
    )

    assert response.status_code == 403


def test_add_duplicate_member_returns_400() -> None:
    owner_token, _ = _register_and_login("owner4")
    _, member_id = _register_and_login("member4")
    household_id = client.post(
        "/households", json={"name": "Smith Family"}, headers=_auth(owner_token)
    ).json()["id"]
    client.post(
        f"/households/{household_id}/members",
        json={"user_id": member_id, "household_role": "adult_member"},
        headers=_auth(owner_token),
    )

    response = client.post(
        f"/households/{household_id}/members",
        json={"user_id": member_id, "household_role": "adult_member"},
        headers=_auth(owner_token),
    )

    assert response.status_code == 400


def test_remove_owner_returns_400() -> None:
    owner_token, owner_id = _register_and_login("owner5")
    household_id = client.post(
        "/households", json={"name": "Smith Family"}, headers=_auth(owner_token)
    ).json()["id"]

    response = client.delete(
        f"/households/{household_id}/members/{owner_id}", headers=_auth(owner_token)
    )

    assert response.status_code == 400


def test_remove_self_as_adult_member_returns_204() -> None:
    owner_token, _ = _register_and_login("owner6")
    member_token, member_id = _register_and_login("member6")
    household_id = client.post(
        "/households", json={"name": "Smith Family"}, headers=_auth(owner_token)
    ).json()["id"]
    client.post(
        f"/households/{household_id}/members",
        json={"user_id": member_id, "household_role": "adult_member"},
        headers=_auth(owner_token),
    )

    response = client.delete(
        f"/households/{household_id}/members/{member_id}", headers=_auth(member_token)
    )

    assert response.status_code == 204


def test_list_my_households_returns_households_for_current_user() -> None:
    token, _ = _register_and_login("owner7")
    client.post("/households", json={"name": "House A"}, headers=_auth(token))
    client.post("/households", json={"name": "House B"}, headers=_auth(token))

    response = client.get("/households", headers=_auth(token))

    assert response.status_code == 200
    assert {h["name"] for h in response.json()} == {"House A", "House B"}


def test_create_child_account_happy_path() -> None:
    token, guardian_id = _register_and_login("guardian1")
    household_id = client.post(
        "/households", json={"name": "Smith Family"}, headers=_auth(token)
    ).json()["id"]

    response = client.post(
        f"/households/{household_id}/children",
        json={
            "username": "kiddo1",
            "email": "kiddo1@example.com",
            "password": "correct-password",
            "age_band": "6-9",
            "policy_version": "v1",
            "evidence": "guardian confirmed via API request",
        },
        headers=_auth(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["child"]["account_type"] == "minor"
    assert body["relationship"]["guardian_user_id"] == guardian_id
    assert body["relationship"]["status"] == "active"
    assert body["learning_profile"]["age_band"] == "6-9"
    assert body["consent_record"]["consented_by_user_id"] == guardian_id


def test_create_child_account_rejects_non_manager_actor() -> None:
    owner_token, _ = _register_and_login("owner8")
    member_token, member_id = _register_and_login("member8")
    household_id = client.post(
        "/households", json={"name": "Smith Family"}, headers=_auth(owner_token)
    ).json()["id"]
    client.post(
        f"/households/{household_id}/members",
        json={"user_id": member_id, "household_role": "adult_member"},
        headers=_auth(owner_token),
    )

    response = client.post(
        f"/households/{household_id}/children",
        json={
            "username": "kiddo2",
            "email": "kiddo2@example.com",
            "password": "correct-password",
            "age_band": "10-13",
            "policy_version": "v1",
            "evidence": "evidence",
        },
        headers=_auth(member_token),
    )

    assert response.status_code == 403


def test_create_child_account_requires_recent_auth() -> None:
    token, guardian_id = _register_and_login("guardian2")
    household_id = client.post(
        "/households", json={"name": "Smith Family"}, headers=_auth(token)
    ).json()["id"]
    stale_token = _stale_access_token(guardian_id, "guardian2")

    response = client.post(
        f"/households/{household_id}/children",
        json={
            "username": "kiddo3",
            "email": "kiddo3@example.com",
            "password": "correct-password",
            "age_band": "10-13",
            "policy_version": "v1",
            "evidence": "evidence",
        },
        headers=_auth(stale_token),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "step_up_required"
