"""Tests for the financial snapshot application service."""

from decimal import Decimal

import pytest

from src.financial.accounts import service as account_service
from src.financial.application.financial_snapshot_service import (
    build_financial_snapshot,
)
from src.financial.bills import service as bill_service
from src.financial.budgets import service as budget_service
from src.financial.budgets.models import Budget
from src.financial.debt import service as debt_service
from src.financial.expenses import service as expense_service
from src.financial.expenses.models import Expense
from src.financial.goals import service as goal_service
from src.financial.goals.models import Goal
from src.financial.income import service as income_service
from src.financial.shared.categories import ExpenseCategory

USER_ID = 1


def test_build_financial_snapshot_with_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build a financial snapshot from populated service data."""

    test_expenses = [
        Expense(
            id=1,
            name="Groceries",
            category=ExpenseCategory.FOOD,
            amount=Decimal("100.00"),
        ),
        Expense(
            id=2,
            name="Gas",
            category=ExpenseCategory.TRANSPORTATION,
            amount=Decimal("50.00"),
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

    test_goals = [
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("2500.00"),
        ),
        Goal(
            id=2,
            name="New Car",
            target_amount=Decimal("30000.00"),
            current_amount=Decimal("5000.00"),
        ),
        Goal(
            id=3,
            name="Vacation",
            target_amount=Decimal("5000.00"),
            current_amount=Decimal("1000.00"),
        ),
    ]

    monkeypatch.setattr(expense_service, "expenses", {USER_ID: test_expenses})
    monkeypatch.setattr(budget_service, "budgets", {USER_ID: test_budgets})
    monkeypatch.setattr(goal_service, "goals", {USER_ID: test_goals})

    monkeypatch.setattr(income_service, "income_entries", {USER_ID: []})
    monkeypatch.setattr(account_service, "accounts", {USER_ID: []})
    monkeypatch.setattr(debt_service, "debts", {USER_ID: []})
    monkeypatch.setattr(bill_service, "bills", {USER_ID: []})

    snapshot = build_financial_snapshot(USER_ID)

    assert snapshot.total_expenses == Decimal("150.00")
    assert snapshot.average_expense == Decimal("75.00")
    assert snapshot.highest_expense == test_expenses[0]
    assert snapshot.lowest_expense == test_expenses[1]

    assert snapshot.category_totals == {
        "Food": Decimal("100.00"),
        "Transportation": Decimal("50.00"),
    }

    assert snapshot.budget_count == 2
    assert snapshot.goal_count == 3

    assert snapshot.health_score == 60
    assert snapshot.health_status == "Fair"


def test_build_financial_snapshot_without_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build an empty financial snapshot."""

    monkeypatch.setattr(expense_service, "expenses", {USER_ID: []})
    monkeypatch.setattr(budget_service, "budgets", {USER_ID: []})
    monkeypatch.setattr(goal_service, "goals", {USER_ID: []})

    monkeypatch.setattr(income_service, "income_entries", {USER_ID: []})
    monkeypatch.setattr(account_service, "accounts", {USER_ID: []})
    monkeypatch.setattr(debt_service, "debts", {USER_ID: []})
    monkeypatch.setattr(bill_service, "bills", {USER_ID: []})

    snapshot = build_financial_snapshot(USER_ID)

    assert snapshot.total_expenses == Decimal("0")
    assert snapshot.average_expense == Decimal("0")
    assert snapshot.highest_expense is None
    assert snapshot.lowest_expense is None
    assert snapshot.category_totals == {}

    assert snapshot.budget_count == 0
    assert snapshot.goal_count == 0

    assert snapshot.health_score == 65
    assert snapshot.health_status == "Fair"
