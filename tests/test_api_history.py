"""Tests for the financial history API endpoints."""

from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.accounts.service import accounts
from src.financial.bills.service import bills
from src.financial.budgets.service import budgets
from src.financial.debt.service import debts
from src.financial.expenses.service import expenses
from src.financial.goals.service import goals
from src.financial.history.service import clear_history
from src.financial.income.service import income_entries

client = TestClient(app)


def setup_function() -> None:
    """Reset in-memory financial state before each test."""
    clear_history()
    accounts.clear()
    bills.clear()
    budgets.clear()
    debts.clear()
    expenses.clear()
    goals.clear()
    income_entries.clear()


def test_list_history_returns_empty_list() -> None:
    response = client.get("/history")

    assert response.status_code == 200
    assert response.json() == []


def test_get_latest_snapshot_returns_404_when_missing() -> None:
    response = client.get("/history/latest")

    assert response.status_code == 404


def test_create_and_list_snapshot() -> None:
    response = client.post("/history/snapshot")

    assert response.status_code == 201
    created = response.json()

    listed = client.get("/history").json()
    assert listed == [created]


def test_get_latest_snapshot_matches_most_recent() -> None:
    client.post("/history/snapshot")
    second = client.post("/history/snapshot").json()

    response = client.get("/history/latest")

    assert response.status_code == 200
    assert response.json()["timestamp"] == second["timestamp"]


def test_get_trends_with_insufficient_data() -> None:
    client.post("/history/snapshot")

    response = client.get("/history/trends")

    assert response.status_code == 200
    body = response.json()
    assert "net_worth" in body
    assert "overall_momentum" in body
