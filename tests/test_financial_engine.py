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
            amount=5000,
        ),
    ]

    expenses = [
        Expense(
            id=1,
            name="Rent",
            category=ExpenseCategory.HOUSING,
            amount=1200,
        ),
        Expense(
            id=2,
            name="Food",
            category=ExpenseCategory.FOOD,
            amount=300,
        ),
    ]

    budgets = [
        Budget(
            category=ExpenseCategory.FOOD,
            limit=500,
        ),
    ]

    accounts = [
        Account(
            id=1,
            name="Checking",
            account_type="Bank",
            balance=2000,
        ),
    ]

    goals = [
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=10000,
            current_amount=2500,
        ),
    ]

    debts = [
        Debt(
            id=1,
            name="Credit Card",
            balance=1000,
            interest_rate=19.99,
            minimum_payment=50,
        ),
    ]

    bills = [
        Bill(
            id=1,
            name="Electric",
            amount=125,
            due_day=15,
            is_paid=False,
        ),
    ]

    snapshot = build_financial_snapshot(
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
    assert snapshot["total_income"] == 5000
    assert snapshot["total_expenses"] == 1500
    assert snapshot["net_cash_flow"] == 3500
    assert snapshot["average_expense"] == 750
    assert snapshot["total_account_balance"] == 2000
    assert snapshot["total_goal_progress"] == 2500
    assert snapshot["total_debt"] == 1000
    assert snapshot["net_worth"] == 3500

    # Largest expense
    assert snapshot["largest_expense"] is not None
    assert snapshot["largest_expense"]["name"] == "Rent"
    assert snapshot["largest_expense"]["amount"] == 1200

    # Category totals
    assert snapshot["category_totals"]["Housing"] == 1200
    assert snapshot["category_totals"]["Food"] == 300

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
        recommendation["priority"]
        for recommendation in snapshot["recommendations"]
    ]

    priority_order = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
    }

    priority_values = [
        priority_order[priority]
        for priority in priorities
    ]

    assert priority_values == sorted(priority_values, reverse=True)

    # Insights
    assert "insights" in snapshot
    assert isinstance(snapshot["insights"], list)