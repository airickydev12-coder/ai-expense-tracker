"""Tests for the income API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.income.service import income_entries

client = TestClient(app)


@pytest.fixture(autouse=True)
def _authenticate() -> None:
    """Register and log in a throwaway user, then attach its token to every request."""
    client.post(
        "/auth/register",
        json={
            "username": "income_test_user",
            "email": "income_test_user@example.com",
            "password": "correct-password",
        },
    )
    token = client.post(
        "/auth/login",
        json={"username": "income_test_user", "password": "correct-password"},
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"


def setup_function() -> None:
    """Reset in-memory income entries before each test."""
    income_entries.clear()


def test_list_income_returns_empty_list() -> None:
    response = client.get("/income")

    assert response.status_code == 200
    assert response.json() == []


def test_create_income() -> None:
    response = client.post(
        "/income",
        json={
            "source": "Salary",
            "amount": 3000.00,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "source": "Salary",
        "amount": 3000.0,
    }


def test_get_income_by_id() -> None:
    created = client.post(
        "/income",
        json={"source": "Salary", "amount": 3000.00},
    ).json()

    response = client.get(f"/income/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_income_returns_404_when_missing() -> None:
    response = client.get("/income/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Income entry with ID 999 was not found."}


def test_update_income() -> None:
    created = client.post(
        "/income",
        json={"source": "Salary", "amount": 3000.00},
    ).json()

    response = client.put(
        f"/income/{created['id']}",
        json={"amount": 3500.00},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": created["id"],
        "source": "Salary",
        "amount": 3500.0,
    }


def test_update_income_returns_404_when_missing() -> None:
    response = client.put("/income/999", json={"amount": 3500.00})

    assert response.status_code == 404


def test_update_income_rejects_empty_body() -> None:
    created = client.post(
        "/income",
        json={"source": "Salary", "amount": 3000.00},
    ).json()

    response = client.put(f"/income/{created['id']}", json={})

    assert response.status_code == 400


def test_delete_income() -> None:
    created = client.post(
        "/income",
        json={"source": "Salary", "amount": 3000.00},
    ).json()

    response = client.delete(f"/income/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created
    assert client.get("/income").json() == []


def test_delete_income_returns_404_when_missing() -> None:
    response = client.delete("/income/999")

    assert response.status_code == 404
