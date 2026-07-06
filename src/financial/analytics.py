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

def get_highest_expense(expenses: list[Expense]) -> Expense | None:
    """
    Find the expense with the highest amount.

    Args:
        expenses: List of expenses.

    Returns:
        Expense | None: The highest expense, or None if the list is empty.
    """
    if not expenses:
        return None

    return max(expenses, key=lambda expense: expense.amount)
