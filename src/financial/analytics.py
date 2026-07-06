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

def get_lowest_expense(expenses: list[Expense]) -> Expense | None:
    """
    Find the expense with the lowest amount.

    Args:
        expenses: List of expenses.

    Returns:
        Expense | None: The lowest expense, or None if the list is empty.
    """
    if not expenses:
        return None

    return min(expenses, key=lambda expense: expense.amount)

def get_category_totals(expenses: list[Expense]) -> dict[str, float]:
    """
    Calculate total spending by category.

    Args:
        expenses: List of expenses.

    Returns:
        dict[str, float]: Category names mapped to total spending.
    """
    totals: dict[str, float] = {}

    for expense in expenses:
        category_name = expense.category.value

        if category_name not in totals:
            totals[category_name] = 0.0

        totals[category_name] += expense.amount

    return totals
