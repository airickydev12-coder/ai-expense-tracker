"""Tests for the recurring expense template API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.expenses.service import expenses
from src.financial.recurring_expenses.service import recurring_expense_templates

client = TestClient(app)


@pytest.fixture(autouse=True)
def _authenticate() -> None:
    """Register and log in a throwaway user, attaching its token to every request."""
    client.post(
        "/auth/register",
        json={
            "username": "recurring-expenses-user",
            "email": "recurring-expenses-user@example.com",
            "password": "correct-password",
        },
    )
    token = client.post(
        "/auth/login",
        json={"username": "recurring-expenses-user", "password": "correct-password"},
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"


def setup_function() -> None:
    """Reset in-memory recurring expense templates and expenses before each test."""
    recurring_expense_templates.clear()
    expenses.clear()


def test_list_recurring_expense_templates_returns_empty_list() -> None:
    response = client.get("/recurring-expenses")

    assert response.status_code == 200
    assert response.json() == []


def test_create_recurring_expense_template() -> None:
    response = client.post(
        "/recurring-expenses",
        json={
            "name": "Streaming Subscription",
            "category": "Entertainment",
            "amount": 15.99,
            "frequency": "MONTHLY",
            "next_occurrence": "2026-09-01",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Streaming Subscription",
        "category": "Entertainment",
        "amount": 15.99,
        "frequency": "MONTHLY",
        "next_occurrence": "2026-09-01",
        "is_active": True,
    }


def test_get_recurring_expense_template_by_id() -> None:
    created = client.post(
        "/recurring-expenses",
        json={
            "name": "Streaming Subscription",
            "category": "Entertainment",
            "amount": 15.99,
            "frequency": "MONTHLY",
            "next_occurrence": "2026-09-01",
        },
    ).json()

    response = client.get(f"/recurring-expenses/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_recurring_expense_template_returns_404_when_missing() -> None:
    response = client.get("/recurring-expenses/999")

    assert response.status_code == 404


def test_update_recurring_expense_template() -> None:
    created = client.post(
        "/recurring-expenses",
        json={
            "name": "Streaming Subscription",
            "category": "Entertainment",
            "amount": 15.99,
            "frequency": "MONTHLY",
            "next_occurrence": "2026-09-01",
        },
    ).json()

    response = client.put(
        f"/recurring-expenses/{created['id']}",
        json={"amount": 17.99, "is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["amount"] == 17.99
    assert response.json()["is_active"] is False


def test_update_recurring_expense_template_returns_404_when_missing() -> None:
    response = client.put("/recurring-expenses/999", json={"amount": 17.99})

    assert response.status_code == 404


def test_update_recurring_expense_template_rejects_empty_body() -> None:
    created = client.post(
        "/recurring-expenses",
        json={
            "name": "Streaming Subscription",
            "category": "Entertainment",
            "amount": 15.99,
            "frequency": "MONTHLY",
            "next_occurrence": "2026-09-01",
        },
    ).json()

    response = client.put(f"/recurring-expenses/{created['id']}", json={})

    assert response.status_code == 400


def test_delete_recurring_expense_template() -> None:
    created = client.post(
        "/recurring-expenses",
        json={
            "name": "Streaming Subscription",
            "category": "Entertainment",
            "amount": 15.99,
            "frequency": "MONTHLY",
            "next_occurrence": "2026-09-01",
        },
    ).json()

    response = client.delete(f"/recurring-expenses/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created
    assert client.get("/recurring-expenses").json() == []


def test_delete_recurring_expense_template_returns_404_when_missing() -> None:
    response = client.delete("/recurring-expenses/999")

    assert response.status_code == 404


def test_generate_due_expenses() -> None:
    client.post(
        "/recurring-expenses",
        json={
            "name": "Streaming Subscription",
            "category": "Entertainment",
            "amount": 15.99,
            "frequency": "MONTHLY",
            "next_occurrence": "2020-01-01",
        },
    )

    response = client.post("/recurring-expenses/generate")

    assert response.status_code == 200
    body = response.json()
    assert body["generated_count"] >= 1
    assert len(body["expense_ids"]) == body["generated_count"]
