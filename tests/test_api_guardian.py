"""Tests for GET /guardian/children."""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


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


def test_list_children_empty_for_guardian_with_none() -> None:
    token, _ = _register_and_login("guardian_empty")

    response = client.get("/guardian/children", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() == []


def test_list_children_returns_linked_children() -> None:
    token, guardian_id = _register_and_login("guardian_with_kids")
    household_id = client.post(
        "/households", json={"name": "Smith Family"}, headers=_auth(token)
    ).json()["id"]
    client.post(
        f"/households/{household_id}/children",
        json={
            "username": "linkedkid",
            "email": "linkedkid@example.com",
            "password": "correct-password",
            "age_band": "6-9",
            "policy_version": "v1",
            "evidence": "evidence",
        },
        headers=_auth(token),
    )

    response = client.get("/guardian/children", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["child"]["username"] == "linkedkid"
    assert body[0]["relationship"]["guardian_user_id"] == guardian_id


def test_list_children_excludes_other_guardians_children() -> None:
    token_a, _ = _register_and_login("guardian_a")
    token_b, _ = _register_and_login("guardian_b")
    household_id = client.post(
        "/households", json={"name": "House A"}, headers=_auth(token_a)
    ).json()["id"]
    client.post(
        f"/households/{household_id}/children",
        json={
            "username": "childofa",
            "email": "childofa@example.com",
            "password": "correct-password",
            "age_band": "6-9",
            "policy_version": "v1",
            "evidence": "evidence",
        },
        headers=_auth(token_a),
    )

    response = client.get("/guardian/children", headers=_auth(token_b))

    assert response.status_code == 200
    assert response.json() == []
