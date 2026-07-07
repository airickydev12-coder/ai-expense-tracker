from src.financial.accounts.models import Account
from src.financial.budgets.models import Budget
from src.financial.debt.models import Debt
from src.financial.expenses.analytics import get_total
from src.financial.expenses.models import Expense
from src.financial.goals.models import Goal
from src.financial.income.analytics import get_total_income
from src.financial.income.models import Income
from src.financial.reports.budget_report import build_budget_report


def build_financial_snapshot(
    income_entries: list[Income],
    expenses: list[Expense],
    budgets: list[Budget],
    accounts: list[Account],
    goals: list[Goal],
    debts: list[Debt],
) -> dict:
    """Build a complete financial snapshot."""
    total_income = get_total_income(income_entries)
    total_expenses = get_total(expenses)
    net_cash_flow = total_income - total_expenses
    total_account_balance = sum(account.balance for account in accounts)
    total_goal_progress = sum(goal.current_amount for goal in goals)
    total_debt = sum(debt.balance for debt in debts)
    net_worth = total_account_balance + total_goal_progress - total_debt
    budget_report = build_budget_report(budgets, expenses)

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_cash_flow": net_cash_flow,
        "total_account_balance": total_account_balance,
        "total_goal_progress": total_goal_progress,
        "total_debt": total_debt,
        "net_worth": net_worth,
        "budget_report": budget_report,
    }