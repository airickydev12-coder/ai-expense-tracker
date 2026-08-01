from decimal import Decimal

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
from src.financial.history.service import clear_history
from src.financial.income.models import Income
from src.financial.income.service import income_entries
from src.financial.scenarios.workspace import (
    scenario_workspace,
)
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
    clear_history()
    scenario_workspace.clear()


def test_load_financial_state_loads_scenario_workspace(
    monkeypatch,
):
    from src.financial.application import financial_state

    captured = {
        "loaded": False,
    }

    monkeypatch.setattr(
        financial_state,
        "load_expenses",
        lambda: None,
    )
    monkeypatch.setattr(
        financial_state,
        "load_budgets",
        lambda: None,
    )
    monkeypatch.setattr(
        financial_state,
        "load_income",
        lambda: None,
    )
    monkeypatch.setattr(
        financial_state,
        "load_accounts",
        lambda: None,
    )
    monkeypatch.setattr(
        financial_state,
        "load_goals",
        lambda: None,
    )
    monkeypatch.setattr(
        financial_state,
        "load_debts",
        lambda: None,
    )
    monkeypatch.setattr(
        financial_state,
        "load_bills",
        lambda: None,
    )
    monkeypatch.setattr(
        financial_state,
        "load_recommendation_history",
        lambda: None,
    )
    monkeypatch.setattr(
        financial_state,
        "load_history",
        lambda: None,
    )

    def fake_load_workspace():
        captured["loaded"] = True

    monkeypatch.setattr(
        financial_state,
        "load_scenario_workspace",
        fake_load_workspace,
    )

    financial_state.load_financial_state()

    assert captured["loaded"] is True


def test_get_financial_state_returns_all_domains():
    income_entries.append(
        Income(
            id=1,
            source="Salary",
            amount=Decimal("5000.00"),
        )
    )

    expenses.append(
        Expense(
            id=1,
            name="Rent",
            category=ExpenseCategory.HOUSING,
            amount=Decimal("1200.00"),
        )
    )

    budgets.append(
        Budget(
            category=ExpenseCategory.HOUSING,
            limit=Decimal("1500.00"),
        )
    )

    accounts.append(
        Account(
            id=1,
            name="Checking",
            account_type="Bank",
            balance=Decimal("1000.00"),
        )
    )

    goals.append(
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("2500.00"),
        )
    )

    debts.append(
        Debt(
            id=1,
            name="Credit Card",
            balance=Decimal("1000.00"),
            interest_rate=19.99,
            minimum_payment=Decimal("50.00"),
        )
    )

    bills.append(
        Bill(
            id=1,
            name="Electric",
            amount=Decimal("125.00"),
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
            amount=Decimal("5000.00"),
        )
    )

    expenses.append(
        Expense(
            id=1,
            name="Rent",
            category=ExpenseCategory.HOUSING,
            amount=Decimal("1200.00"),
        )
    )

    budgets.append(
        Budget(
            category=ExpenseCategory.HOUSING,
            limit=Decimal("1500.00"),
        )
    )

    accounts.append(
        Account(
            id=1,
            name="Checking",
            account_type="Bank",
            balance=Decimal("2000.00"),
        )
    )

    goals.append(
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("2500.00"),
        )
    )

    debts.append(
        Debt(
            id=1,
            name="Credit Card",
            balance=Decimal("1000.00"),
            interest_rate=19.99,
            minimum_payment=Decimal("50.00"),
        )
    )

    bills.append(
        Bill(
            id=1,
            name="Electric",
            amount=Decimal("125.00"),
            due_day=15,
            is_paid=False,
        )
    )

    snapshot = build_current_financial_snapshot(
        current_day=10,
    )

    assert snapshot["total_income"] == Decimal("5000.00")
    assert snapshot["total_expenses"] == Decimal("1200.00")
    assert snapshot["net_cash_flow"] == Decimal("3800.00")
    assert snapshot["total_account_balance"] == Decimal("2000.00")
    assert snapshot["total_goal_progress"] == Decimal("2500.00")
    assert snapshot["total_debt"] == Decimal("1000.00")
    assert len(snapshot["bills"]) == 1
    assert snapshot["current_day"] == 10
    assert "recommendations" in snapshot


def test_record_current_financial_snapshot(
    monkeypatch,
):
    from src.financial.application import financial_state

    captured_snapshot: dict = {}

    fake_snapshot = {
        "total_income": Decimal("5000.00"),
        "total_expenses": Decimal("1500.00"),
        "net_cash_flow": Decimal("3500.00"),
        "total_account_balance": Decimal("2000.00"),
        "total_goal_progress": Decimal("2500.00"),
        "total_debt": Decimal("1000.00"),
        "net_worth": Decimal("3500.00"),
        "health_score": 85,
        "health_status": "Excellent",
        "accounts": [
            {
                "id": 1,
                "name": "Checking",
            }
        ],
        "goals": [
            {
                "id": 1,
                "name": "Emergency Fund",
            }
        ],
        "debts": [
            {
                "id": 1,
                "name": "Credit Card",
            }
        ],
        "bills": [
            {
                "id": 1,
                "name": "Electric",
            }
        ],
        "current_day": 10,
        "recommendations": [],
    }

    monkeypatch.setattr(
        financial_state,
        "build_current_financial_snapshot",
        lambda current_day=None: fake_snapshot,
    )

    def fake_record(snapshot):
        captured_snapshot.update(snapshot)
        return "recorded"

    monkeypatch.setattr(
        financial_state,
        "record_snapshot",
        fake_record,
    )

    snapshot, record = financial_state.record_current_financial_snapshot()

    assert snapshot == fake_snapshot
    assert record == "recorded"
    assert captured_snapshot["net_worth"] == Decimal("3500.00")

    assert snapshot["total_income"] == Decimal("5000.00")
    assert snapshot["total_expenses"] == Decimal("1500.00")
    assert snapshot["net_cash_flow"] == Decimal("3500.00")
    assert snapshot["total_account_balance"] == Decimal("2000.00")
    assert snapshot["total_goal_progress"] == Decimal("2500.00")
    assert snapshot["total_debt"] == Decimal("1000.00")
    assert len(snapshot["bills"]) == 1
    assert snapshot["current_day"] == 10
    assert "recommendations" in snapshot
