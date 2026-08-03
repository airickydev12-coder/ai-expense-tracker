"""Tests for the budget API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.budgets.service import budgets
from src.financial.shared.categories import ExpenseCategory

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
    """Reset in-memory budgets before each test."""
    budgets.clear()


def test_get_budgets_returns_empty_list() -> None:
    response = client.get("/budgets")

    assert response.status_code == 200
    assert response.json() == []


def test_create_budget() -> None:
    response = client.post(
        "/budgets",
        json={
            "category": ExpenseCategory.FOOD.value,
            "limit": 500,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "category": ExpenseCategory.FOOD.value,
        "limit": 500.0,
    }


def test_get_budget_by_category() -> None:
    client.post(
        "/budgets",
        json={
            "category": ExpenseCategory.FOOD.value,
            "limit": 500,
        },
    )

    response = client.get(f"/budgets/{ExpenseCategory.FOOD.value}")

    assert response.status_code == 200
    assert response.json() == {
        "category": ExpenseCategory.FOOD.value,
        "limit": 500.0,
    }


def test_get_budget_returns_404_when_missing() -> None:
    response = client.get(f"/budgets/{ExpenseCategory.FOOD.value}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            f"Budget for category " f"'{ExpenseCategory.FOOD.value}' was not found."
        )
    }


def test_update_budget() -> None:
    client.post(
        "/budgets",
        json={
            "category": ExpenseCategory.FOOD.value,
            "limit": 500,
        },
    )

    response = client.put(
        f"/budgets/{ExpenseCategory.FOOD.value}",
        json={"limit": 750},
    )

    assert response.status_code == 200
    assert response.json() == {
        "category": ExpenseCategory.FOOD.value,
        "limit": 750.0,
    }


def test_update_budget_returns_404_when_missing() -> None:
    response = client.put(
        f"/budgets/{ExpenseCategory.FOOD.value}",
        json={"limit": 750},
    )

    assert response.status_code == 404


def test_delete_budget() -> None:
    client.post(
        "/budgets",
        json={
            "category": ExpenseCategory.FOOD.value,
            "limit": 500,
        },
    )

    response = client.delete(f"/budgets/{ExpenseCategory.FOOD.value}")

    assert response.status_code == 200
    assert response.json() == {
        "category": ExpenseCategory.FOOD.value,
        "limit": 500.0,
    }

    assert client.get("/budgets").json() == []


def test_delete_budget_returns_404_when_missing() -> None:
    response = client.delete(f"/budgets/{ExpenseCategory.FOOD.value}")

    assert response.status_code == 404


def test_create_budget_rejects_zero_limit() -> None:
    response = client.post(
        "/budgets",
        json={
            "category": ExpenseCategory.FOOD.value,
            "limit": 0,
        },
    )

    assert response.status_code == 422


def test_create_budget_rejects_negative_limit() -> None:
    response = client.post(
        "/budgets",
        json={
            "category": ExpenseCategory.FOOD.value,
            "limit": -10,
        },
    )

    assert response.status_code == 422


def test_update_budget_rejects_zero_limit() -> None:
    response = client.put(
        f"/budgets/{ExpenseCategory.FOOD.value}",
        json={"limit": 0},
    )

    assert response.status_code == 422


def test_invalid_category_returns_422() -> None:
    response = client.get("/budgets/not-a-category")

    assert response.status_code == 422
