from src.financial.accounts.models import Account
from src.financial.budgets.models import Budget
from src.financial.debt.models import Debt
from src.financial.engine.financial_engine import build_financial_snapshot
from src.financial.expenses.models import Expense
from src.financial.goals.models import Goal
from src.financial.income.models import Income
from src.financial.shared.categories import ExpenseCategory


def test_build_financial_snapshot():
    income_entries = [
        Income(id=1, source="Salary", amount=5000),
    ]

    expenses = [
        Expense(id=1, name="Rent", category=ExpenseCategory.HOUSING, amount=1200),
        Expense(id=2, name="Food", category=ExpenseCategory.FOOD, amount=300),
    ]

    budgets = [
        Budget(category=ExpenseCategory.FOOD, limit=500),
    ]

    accounts = [
        Account(id=1, name="Checking", account_type="Bank", balance=2000),
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

    snapshot = build_financial_snapshot(
        income_entries=income_entries,
        expenses=expenses,
        budgets=budgets,
        accounts=accounts,
        goals=goals,
        debts=debts,
    )

    assert snapshot["total_income"] == 5000
    assert snapshot["total_expenses"] == 1500
    assert snapshot["net_cash_flow"] == 3500
    assert snapshot["total_account_balance"] == 2000
    assert snapshot["total_goal_progress"] == 2500
    assert snapshot["total_debt"] == 1000
    assert snapshot["net_worth"] == 3500
    assert len(snapshot["budget_report"]) == 1