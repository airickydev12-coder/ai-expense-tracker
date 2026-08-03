"""Tests for the goal and goal-ledger API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.goals.service import goals

client = TestClient(app)


@pytest.fixture(autouse=True)
def _authenticate() -> None:
    """Register and log in a throwaway user, authenticating `client` for every test."""
    client.post(
        "/auth/register",
        json={"username": "testuser", "email": "testuser@example.com", "password": "correct-password"},
    )
    token = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "correct-password"},
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"


def setup_function() -> None:
    """Reset in-memory goals before each test."""
    goals.clear()


def _create_goal(target_amount: float = 1000, current_amount: float = 0) -> dict:
    return client.post(
        "/goals",
        json={
            "name": "Emergency Fund",
            "target_amount": target_amount,
            "current_amount": current_amount,
        },
    ).json()


def test_list_goals_returns_empty_list() -> None:
    response = client.get("/goals")

    assert response.status_code == 200
    assert response.json() == []


def test_create_goal() -> None:
    response = client.post(
        "/goals",
        json={"name": "Emergency Fund", "target_amount": 1000},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Emergency Fund",
        "target_amount": 1000.0,
        "current_amount": 0.0,
    }


def test_get_goal_returns_404_when_missing() -> None:
    response = client.get("/goals/999")

    assert response.status_code == 404


def test_update_goal() -> None:
    created = _create_goal()

    response = client.put(
        f"/goals/{created['id']}",
        json={"target_amount": 2000},
    )

    assert response.status_code == 200
    assert response.json()["target_amount"] == 2000.0


def test_contribute_to_goal() -> None:
    created = _create_goal(target_amount=1000)

    response = client.post(
        f"/goals/{created['id']}/contributions",
        json={"amount": 250},
    )

    assert response.status_code == 200
    assert response.json()["current_amount"] == 250.0


def test_contribute_to_goal_returns_404_when_missing() -> None:
    response = client.post("/goals/999/contributions", json={"amount": 250})

    assert response.status_code == 404


def test_withdraw_from_goal() -> None:
    created = _create_goal(target_amount=1000, current_amount=500)

    response = client.post(
        f"/goals/{created['id']}/withdrawals",
        json={"amount": 200},
    )

    assert response.status_code == 200
    assert response.json()["current_amount"] == 300.0


def test_withdraw_more_than_balance_returns_400() -> None:
    created = _create_goal(target_amount=1000, current_amount=100)

    response = client.post(
        f"/goals/{created['id']}/withdrawals",
        json={"amount": 200},
    )

    assert response.status_code == 400


def test_adjust_goal_balance() -> None:
    created = _create_goal(target_amount=1000, current_amount=500)

    response = client.post(
        f"/goals/{created['id']}/adjustments",
        json={"amount": -50},
    )

    assert response.status_code == 200
    assert response.json()["current_amount"] == 450.0


def test_reverse_goal_ledger_entry() -> None:
    created = _create_goal(target_amount=1000)

    contributed = client.post(
        f"/goals/{created['id']}/contributions",
        json={"amount": 250},
    ).json()
    assert contributed["current_amount"] == 250.0

    ledger = client.get(f"/goals/{created['id']}/ledger").json()
    contribution_entry = next(
        entry for entry in ledger if entry["entry_type"] == "CONTRIBUTION"
    )

    response = client.post(
        f"/goals/{created['id']}/reversals",
        json={"entry_id": contribution_entry["entry_id"]},
    )

    assert response.status_code == 200
    assert response.json()["current_amount"] == 0.0


def test_reverse_unknown_entry_returns_404() -> None:
    created = _create_goal(target_amount=1000)

    response = client.post(
        f"/goals/{created['id']}/reversals",
        json={"entry_id": "00000000-0000-0000-0000-000000000000"},
    )

    assert response.status_code == 404


def test_get_goal_ledger() -> None:
    created = _create_goal(target_amount=1000)
    client.post(f"/goals/{created['id']}/contributions", json={"amount": 250})

    response = client.get(f"/goals/{created['id']}/ledger")

    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["entry_type"] == "CONTRIBUTION"
    assert entries[0]["amount"] == 250.0


def test_reconcile_goal() -> None:
    created = _create_goal(target_amount=1000)
    client.post(f"/goals/{created['id']}/contributions", json={"amount": 250})

    response = client.get(f"/goals/{created['id']}/reconcile")

    assert response.status_code == 200
    assert response.json() == {"is_reconciled": True, "ledger_balance": 250.0}


def test_delete_goal() -> None:
    created = _create_goal()

    response = client.delete(f"/goals/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created
    assert client.get("/goals").json() == []


def test_delete_goal_returns_404_when_missing() -> None:
    response = client.delete("/goals/999")

    assert response.status_code == 404
