from src.financial.expenses.analytics import get_total
from src.financial.expenses.models import Expense
from src.financial.income.analytics import get_total_income
from src.financial.income.models import Income


def calculate_cash_flow(
    income_entries: list[Income],
    expenses: list[Expense],
) -> dict:
    """Calculate income, expenses, and net cash flow."""
    total_income = get_total_income(income_entries)
    total_expenses = get_total(expenses)

    return {
        "income": total_income,
        "expenses": total_expenses,
        "net_cash_flow": total_income - total_expenses,
    }