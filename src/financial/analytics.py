from src.financial.models import Expense


def get_total(expenses: list[Expense]) -> float:
    """Calculate the total amount of all expenses."""
    return sum(expense.amount for expense in expenses)


def get_average(expenses: list[Expense]) -> float:
    """
    Calculate the average expense amount.

    Args:
        expenses: List of expenses.

    Returns:
        float: Average expense amount.
    """
    if not expenses:
        return 0.0

    return get_total(expenses) / len(expenses)