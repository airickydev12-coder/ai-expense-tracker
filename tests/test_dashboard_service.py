"""Tests for the dashboard application service."""

from decimal import Decimal

import pytest

from src.financial.application.dashboard_service import (
    Dashboard,
    build_dashboard,
)
from src.financial.budgets import service as budget_service
from src.financial.budgets.models import Budget
from src.financial.expenses import service as expense_service
from src.financial.expenses.models import Expense
from src.financial.shared.categories import ExpenseCategory


def test_build_dashboard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build a dashboard from sample financial data."""

    test_expenses = [
        Expense(
            id=1,
            name="Groceries",
            amount=Decimal("100.00"),
            category=ExpenseCategory.FOOD,
        ),
        Expense(
            id=2,
            name="Gas",
            amount=Decimal("50.00"),
            category=ExpenseCategory.TRANSPORTATION,
        ),
    ]

    test_budgets = [
        Budget(
            category=ExpenseCategory.FOOD,
            limit=Decimal("500.00"),
        ),
        Budget(
            category=ExpenseCategory.TRANSPORTATION,
            limit=Decimal("250.00"),
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

    dashboard = build_dashboard()

    assert isinstance(dashboard, Dashboard)

    assert dashboard.total_expenses == Decimal("150.00")
    assert dashboard.average_expense == Decimal("75.00")

    assert dashboard.highest_expense is not None
    assert dashboard.highest_expense.name == "Groceries"

    assert dashboard.lowest_expense is not None
    assert dashboard.lowest_expense.name == "Gas"

    assert dashboard.category_totals == {
        "Food": 100.00,
        "Transportation": Decimal("50.00"),
    }

    assert dashboard.budget_count == 2

    assert dashboard.monthly_budget == Decimal("750.00")
    assert dashboard.remaining_budget == Decimal("600.00")
    assert dashboard.budget_used_percent == Decimal("20.00")

    assert dashboard.recommendation_count == 0

    assert dashboard.health_score == 65
    assert dashboard.health_status == "Fair"
