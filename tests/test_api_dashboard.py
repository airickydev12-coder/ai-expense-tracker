"""Tests for the financial dashboard API."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.budgets import service as budget_service
from src.financial.budgets.models import Budget
from src.financial.expenses import service as expense_service
from src.financial.expenses.models import Expense
from src.financial.shared.categories import ExpenseCategory


client = TestClient(app)


def test_get_dashboard_with_financial_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return dashboard data from existing financial services."""

    test_expenses = [
        Expense(
            id=1,
            name="Groceries",
            category=ExpenseCategory.FOOD,
            amount=100.00,
        ),
        Expense(
            id=2,
            name="Gas",
            category=ExpenseCategory.TRANSPORTATION,
            amount=50.00,
        ),
    ]

    test_budgets = [
        Budget(
            category=ExpenseCategory.FOOD,
            limit=500.00,
        ),
        Budget(
            category=ExpenseCategory.TRANSPORTATION,
            limit=250.00,
        ),
    ]

    monkeypatch.setattr(
        expense_service,
        "expenses",
        test_expenses,
    )

    monkeypatch.setattr(
        budget_service,
        "budgets",
        test_budgets,
    )

    response = client.get("/dashboard")

    assert response.status_code == 200

    data = response.json()

    assert data["total_expenses"] == 150.00
    assert data["average_expense"] == 75.00

    assert data["highest_expense"] is not None
    assert data["highest_expense"]["id"] == 1
    assert data["highest_expense"]["name"] == "Groceries"
    assert data["highest_expense"]["amount"] == 100.00

    assert data["lowest_expense"] is not None
    assert data["lowest_expense"]["id"] == 2
    assert data["lowest_expense"]["name"] == "Gas"
    assert data["lowest_expense"]["amount"] == 50.00

    assert data["category_totals"] == {
        "Food": 100.00,
        "Transportation": 50.00,
    }

    assert data["budget_count"] == 2
    assert data["health_score"] == 65
    assert data["health_status"] == "Fair"


def test_get_dashboard_without_financial_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return an empty dashboard when no financial data exists."""

    monkeypatch.setattr(
        expense_service,
        "expenses",
        [],
    )

    monkeypatch.setattr(
        budget_service,
        "budgets",
        [],
    )

    response = client.get("/dashboard")

    assert response.status_code == 200

    data = response.json()

    assert data["total_expenses"] == 0.0
    assert data["average_expense"] == 0.0
    assert data["highest_expense"] is None
    assert data["lowest_expense"] is None
    assert data["category_totals"] == {}
    assert data["budget_count"] == 0
    assert data["health_score"] == 65
    assert data["health_status"] == "Fair"
