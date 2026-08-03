"""Tests for the debt API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.debt.service import debts

client = TestClient(app)


@pytest.fixture(autouse=True)
def _authenticate() -> None:
    """Register and log in a throwaway user for every test in this file."""
    debts.clear()
    client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "correct-password",
        },
    )
    token = client.post(
        "/auth/login",
        json={"username": "alice", "password": "correct-password"},
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"


def test_list_debts_returns_empty_list() -> None:
    response = client.get("/debts")

    assert response.status_code == 200
    assert response.json() == []


def test_create_debt() -> None:
    response = client.post(
        "/debts",
        json={
            "name": "Credit Card",
            "balance": 2500.00,
            "interest_rate": 24.99,
            "minimum_payment": 75.00,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Credit Card",
        "balance": 2500.0,
        "interest_rate": 24.99,
        "minimum_payment": 75.0,
    }


def test_get_debt_by_id() -> None:
    created = client.post(
        "/debts",
        json={
            "name": "Credit Card",
            "balance": 2500.00,
            "interest_rate": 24.99,
            "minimum_payment": 75.00,
        },
    ).json()

    response = client.get(f"/debts/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_debt_returns_404_when_missing() -> None:
    response = client.get("/debts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Debt with ID 999 was not found."}


def test_update_debt() -> None:
    created = client.post(
        "/debts",
        json={
            "name": "Credit Card",
            "balance": 2500.00,
            "interest_rate": 24.99,
            "minimum_payment": 75.00,
        },
    ).json()

    response = client.put(
        f"/debts/{created['id']}",
        json={"balance": 2000.00},
    )

    assert response.status_code == 200
    assert response.json()["balance"] == 2000.0


def test_update_debt_returns_404_when_missing() -> None:
    response = client.put("/debts/999", json={"balance": 2000.00})

    assert response.status_code == 404


def test_apply_payment_to_debt() -> None:
    created = client.post(
        "/debts",
        json={
            "name": "Credit Card",
            "balance": 2500.00,
            "interest_rate": 24.99,
            "minimum_payment": 75.00,
        },
    ).json()

    response = client.post(
        f"/debts/{created['id']}/payments",
        json={"payment": 500.00},
    )

    assert response.status_code == 200
    assert response.json()["balance"] == 2000.0


def test_apply_payment_to_debt_returns_404_when_missing() -> None:
    response = client.post("/debts/999/payments", json={"payment": 500.00})

    assert response.status_code == 404


def test_apply_negative_payment_returns_400() -> None:
    created = client.post(
        "/debts",
        json={
            "name": "Credit Card",
            "balance": 2500.00,
            "interest_rate": 24.99,
            "minimum_payment": 75.00,
        },
    ).json()

    response = client.post(
        f"/debts/{created['id']}/payments",
        json={"payment": -100.00},
    )

    assert response.status_code == 400
    assert "cannot be negative" in response.json()["detail"]


def test_delete_debt() -> None:
    created = client.post(
        "/debts",
        json={
            "name": "Credit Card",
            "balance": 2500.00,
            "interest_rate": 24.99,
            "minimum_payment": 75.00,
        },
    ).json()

    response = client.delete(f"/debts/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created
    assert client.get("/debts").json() == []


def test_delete_debt_returns_404_when_missing() -> None:
    response = client.delete("/debts/999")

    assert response.status_code == 404
