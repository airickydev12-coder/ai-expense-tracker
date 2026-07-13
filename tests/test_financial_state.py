from src.financial.accounts.models import Account
from src.financial.accounts.service import accounts
from src.financial.application.financial_state import (
    build_current_financial_snapshot,
    get_financial_state,
)
from src.financial.bills.models import Bill
from src.financial.bills.service import bills
from src.financial.budgets.models import Budget
from src.financial.budgets.service import budgets
from src.financial.debt.models import Debt
from src.financial.debt.service import debts
from src.financial.expenses.models import Expense
from src.financial.expenses.service import expenses
from src.financial.goals.models import Goal
from src.financial.goals.service import goals
from src.financial.income.models import Income
from src.financial.income.service import income_entries
from src.financial.shared.categories import ExpenseCategory


def setup_function():
    """Clear all in-memory financial state before each test."""
    income_entries.clear()
    expenses.clear()
    budgets.clear()
    accounts.clear()
    goals.clear()
    debts.clear()
    bills.clear()


def test_get_financial_state_returns_all_domains():
    income_entries.append(
        Income(
            id=1,
            source="Salary",
            amount=5000,
        )
    )

    expenses.append(
        Expense(
            id=1,
            name="Rent",
            category=ExpenseCategory.HOUSING,
            amount=1200,
        )
    )

    budgets.append(
        Budget(
            category=ExpenseCategory.HOUSING,
            limit=1500,
        )
    )

    accounts.append(
        Account(
            id=1,
            name="Checking",
            account_type="Bank",
            balance=2000,
        )
    )

    goals.append(
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=10000,
            current_amount=2500,
        )
    )

    debts.append(
        Debt(
            id=1,
            name="Credit Card",
            balance=1000,
            interest_rate=19.99,
            minimum_payment=50,
        )
    )

    bills.append(
        Bill(
            id=1,
            name="Electric",
            amount=125,
            due_day=15,
            is_paid=False,
        )
    )

    state = get_financial_state()

    assert len(state["income_entries"]) == 1
    assert len(state["expenses"]) == 1
    assert len(state["budgets"]) == 1
    assert len(state["accounts"]) == 1
    assert len(state["goals"]) == 1
    assert len(state["debts"]) == 1
    assert len(state["bills"]) == 1


def test_build_current_financial_snapshot():
    income_entries.append(
        Income(
            id=1,
            source="Salary",
            amount=5000,
        )
    )

    expenses.append(
        Expense(
            id=1,
            name="Rent",
            category=ExpenseCategory.HOUSING,
            amount=1200,
        )
    )

    budgets.append(
        Budget(
            category=ExpenseCategory.HOUSING,
            limit=1500,
        )
    )

    accounts.append(
        Account(
            id=1,
            name="Checking",
            account_type="Bank",
            balance=2000,
        )
    )

    goals.append(
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=10000,
            current_amount=2500,
        )
    )

    debts.append(
        Debt(
            id=1,
            name="Credit Card",
            balance=1000,
            interest_rate=19.99,
            minimum_payment=50,
        )
    )

    bills.append(
        Bill(
            id=1,
            name="Electric",
            amount=125,
            due_day=15,
            is_paid=False,
        )
    )

    snapshot = build_current_financial_snapshot(
        current_day=10,
    )

    assert snapshot["total_income"] == 5000
    assert snapshot["total_expenses"] == 1200
    assert snapshot["net_cash_flow"] == 3800
    assert snapshot["total_account_balance"] == 2000
    assert snapshot["total_goal_progress"] == 2500
    assert snapshot["total_debt"] == 1000
    assert len(snapshot["bills"]) == 1
    assert snapshot["current_day"] == 10
    assert "recommendations" in snapshot