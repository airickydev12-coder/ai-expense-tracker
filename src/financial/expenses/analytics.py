from decimal import Decimal

from src.financial.expenses.models import Expense


def get_total(expenses: list[Expense]) -> Decimal:
    """Calculate the total amount of all expenses."""
    return sum((expense.amount for expense in expenses), Decimal("0"))


def get_average(expenses: list[Expense]) -> Decimal:
    """
    Calculate the average expense amount.

    Args:
        expenses: List of expenses.

    Returns:
        Decimal: Average expense amount.
    """
    if not expenses:
        return Decimal("0")

    return get_total(expenses) / Decimal(len(expenses))


def get_highest_expense(expenses: list[Expense]) -> Expense | None:
    """
    Find the expense with the highest amount.
    """
    if not expenses:
        return None

    return max(expenses, key=lambda expense: expense.amount)


def get_lowest_expense(expenses: list[Expense]) -> Expense | None:
    """
    Find the expense with the lowest amount.
    """
    if not expenses:
        return None

    return min(expenses, key=lambda expense: expense.amount)


def get_category_totals(expenses: list[Expense]) -> dict[str, Decimal]:
    """
    Calculate total spending by category.

    Args:
        expenses: List of expenses.

    Returns:
        dict[str, Decimal]: Category names mapped to total spending.
    """
    totals: dict[str, Decimal] = {}

    for expense in expenses:
        category_name = expense.category.value

        if category_name not in totals:
            totals[category_name] = Decimal("0")

        totals[category_name] += expense.amount

    return totals
