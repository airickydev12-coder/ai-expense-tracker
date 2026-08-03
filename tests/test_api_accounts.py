"""Tests for the account API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.accounts.service import accounts

client = TestClient(app)


@pytest.fixture(autouse=True)
def _authenticate() -> None:
    """Register and log in a throwaway user, then attach its bearer token
    to every request this client makes for the rest of the test."""
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


def setup_function() -> None:
    """Reset in-memory accounts before each test."""
    accounts.clear()


def test_list_accounts_returns_empty_list() -> None:
    response = client.get("/accounts")

    assert response.status_code == 200
    assert response.json() == []


def test_create_account() -> None:
    response = client.post(
        "/accounts",
        json={
            "name": "Checking",
            "account_type": "Bank",
            "balance": 1500,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Checking",
        "account_type": "Bank",
        "balance": 1500.0,
    }


def test_get_account_by_id() -> None:
    created = client.post(
        "/accounts",
        json={
            "name": "Checking",
            "account_type": "Bank",
            "balance": 1500,
        },
    ).json()

    response = client.get(f"/accounts/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_account_returns_404_when_missing() -> None:
    response = client.get("/accounts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Account with ID 999 was not found."}


def test_update_account() -> None:
    created = client.post(
        "/accounts",
        json={
            "name": "Checking",
            "account_type": "Bank",
            "balance": 1500,
        },
    ).json()

    response = client.put(
        f"/accounts/{created['id']}",
        json={"balance": 2000},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": created["id"],
        "name": "Checking",
        "account_type": "Bank",
        "balance": 2000.0,
    }


def test_update_account_returns_404_when_missing() -> None:
    response = client.put("/accounts/999", json={"balance": 2000})

    assert response.status_code == 404


def test_update_account_rejects_empty_body() -> None:
    created = client.post(
        "/accounts",
        json={
            "name": "Checking",
            "account_type": "Bank",
            "balance": 1500,
        },
    ).json()

    response = client.put(f"/accounts/{created['id']}", json={})

    assert response.status_code == 400


def test_delete_account() -> None:
    created = client.post(
        "/accounts",
        json={
            "name": "Checking",
            "account_type": "Bank",
            "balance": 1500,
        },
    ).json()

    response = client.delete(f"/accounts/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created
    assert client.get("/accounts").json() == []


def test_delete_account_returns_404_when_missing() -> None:
    response = client.delete("/accounts/999")

    assert response.status_code == 404
