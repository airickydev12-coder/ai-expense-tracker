from src.financial.models import Expense
from src.financial.repository import (
    load_expenses_from_file,
    save_expenses_to_file,
)

expenses: list[Expense] = []


def load_expenses() -> None:
    """Load expenses from the repository."""
    global expenses
    expenses = load_expenses_from_file()


def save_expenses() -> None:
    """Save expenses using the repository."""
    save_expenses_to_file(expenses)


def get_next_expense_id() -> int:
    """Return the next available expense ID."""
    if not expenses:
        return 1

    return max(expense.id for expense in expenses) + 1


def add_expense(name: str, category: str, amount: float) -> Expense:
    """Create and add a new expense."""
    expense = Expense(
        id=get_next_expense_id(),
        name=name,
        category=category,
        amount=amount,
    )

    expenses.append(expense)
    save_expenses()

    return expense


def get_expenses() -> list[Expense]:
    """Return a copy of all recorded expenses."""
    return expenses.copy()


def delete_expense(expense_id: int) -> Expense | None:
    """
    Delete an expense by ID.

    Args:
        expense_id: The ID of the expense to delete.

    Returns:
        Expense | None: The deleted expense, or None if not found.
    """
    for index, expense in enumerate(expenses):
        if expense.id == expense_id:
            deleted_expense = expenses.pop(index)
            save_expenses()
            return deleted_expense

    return None


def update_expense(
    expense_id: int,
    name: str | None = None,
    category: str | None = None,
    amount: float | None = None,
) -> Expense | None:
    """Update an existing expense by ID."""
    for expense in expenses:
        if expense.id == expense_id:
            if name is not None:
                expense.name = name

            if category is not None:
                expense.category = category

            if amount is not None:
                expense.amount = amount

            save_expenses()
            return expense

    return None




def calculate_total() -> None:
    """
    Display the total amount of all recorded expenses.

    Retrieves the total spending by calling the get_total()
    function and prints the result formatted as currency.

    Returns:
        None
    """
    total = get_total()
    print(f"Total spending: ${total:.2f}")