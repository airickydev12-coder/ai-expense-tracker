from decimal import Decimal

from src.financial.accounts.models import Account
from src.financial.bills.models import Bill
from src.financial.budgets.models import Budget
from src.financial.debt.models import Debt
from src.financial.engine.financial_engine import build_financial_snapshot
from src.financial.expenses.models import Expense
from src.financial.goals.models import Goal
from src.financial.income.models import Income
from src.financial.shared.categories import ExpenseCategory


def test_build_financial_snapshot():
    income_entries = [
        Income(
            id=1,
            source="Salary",
            amount=Decimal("5000.00"),
        ),
    ]

    expenses = [
        Expense(
            id=1,
            name="Rent",
            category=ExpenseCategory.HOUSING,
            amount=Decimal("1200.00"),
        ),
        Expense(
            id=2,
            name="Food",
            category=ExpenseCategory.FOOD,
            amount=Decimal("300.00"),
        ),
    ]

    budgets = [
        Budget(
            category=ExpenseCategory.FOOD,
            limit=Decimal("500.00"),
        ),
    ]

    accounts = [
        Account(
            id=1,
            name="Checking",
            account_type="Bank",
            balance=Decimal("2000.00"),
        ),
    ]

    goals = [
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("2500.00"),
        ),
    ]

    debts = [
        Debt(
            id=1,
            name="Credit Card",
            balance=Decimal("1000.00"),
            interest_rate=19.99,
            minimum_payment=Decimal("50.00"),
        ),
    ]

    bills = [
        Bill(
            id=1,
            name="Electric",
            amount=Decimal("125.00"),
            due_day=15,
            is_paid=False,
        ),
    ]

    snapshot = build_financial_snapshot(
        user_id=1,
        income_entries=income_entries,
        expenses=expenses,
        budgets=budgets,
        accounts=accounts,
        goals=goals,
        debts=debts,
        bills=bills,
        current_day=10,
    )

    # Financial metrics
    assert snapshot["total_income"] == Decimal("5000.00")
    assert snapshot["total_expenses"] == Decimal("1500.00")
    assert snapshot["net_cash_flow"] == Decimal("3500.00")
    assert snapshot["average_expense"] == Decimal("750.00")
    assert snapshot["total_account_balance"] == Decimal("2000.00")
    assert snapshot["total_goal_progress"] == Decimal("2500.00")
    assert snapshot["total_debt"] == Decimal("1000.00")
    assert snapshot["net_worth"] == Decimal("3500.00")

    # Largest expense
    assert snapshot["largest_expense"] is not None
    assert snapshot["largest_expense"]["name"] == "Rent"
    assert snapshot["largest_expense"]["amount"] == Decimal("1200.00")

    # Category totals
    assert snapshot["category_totals"]["Housing"] == Decimal("1200.00")
    assert snapshot["category_totals"]["Food"] == Decimal("300.00")

    # Budget report
    assert len(snapshot["budget_report"]) == 1

    # Health
    assert snapshot["health_score"] == 85
    assert snapshot["health_status"] == "Excellent"

    # Accounts
    assert len(snapshot["accounts"]) == 1
    assert snapshot["accounts"][0]["name"] == "Checking"

    # Goals
    assert len(snapshot["goals"]) == 1
    assert snapshot["goals"][0]["name"] == "Emergency Fund"

    # Debts
    assert len(snapshot["debts"]) == 1
    assert snapshot["debts"][0]["name"] == "Credit Card"

    # Bills
    assert len(snapshot["bills"]) == 1
    assert snapshot["bills"][0]["name"] == "Electric"
    assert snapshot["current_day"] == 10

    # Recommendations
    assert "recommendations" in snapshot
    assert isinstance(snapshot["recommendations"], list)

    priorities = [
        recommendation["priority"] for recommendation in snapshot["recommendations"]
    ]

    priority_order = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
    }

    priority_values = [priority_order[priority] for priority in priorities]

    assert priority_values == sorted(priority_values, reverse=True)

    # Insights
    assert "insights" in snapshot
    assert isinstance(snapshot["insights"], list)
