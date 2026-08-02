from decimal import Decimal

from src.core.logging import get_logger
from src.financial.events.bus import event_bus
from src.financial.events.event_types import FinancialEvent
from src.financial.expenses.models import Expense
from src.financial.expenses.repository import (
    load_expenses_from_file,
    save_expenses_to_file,
)
from src.financial.shared.categories import ExpenseCategory

logger = get_logger(__name__)

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


def add_expense(
    name: str,
    category: ExpenseCategory,
    amount: Decimal,
) -> Expense:
    """Create and add a new expense."""
    expense = Expense(
        id=get_next_expense_id(),
        name=name,
        category=category,
        amount=amount,
    )

    expenses.append(expense)
    save_expenses()

    event_bus.publish(FinancialEvent.EXPENSE_ADDED, expense)

    logger.info(
        "Added expense %d (%s, %s)",
        expense.id,
        expense.name,
        expense.category.value,
    )

    return expense


def get_expenses() -> list[Expense]:
    """Return a copy of all recorded expenses."""
    return expenses.copy()


def get_expense_by_id(
    expense_id: int,
) -> Expense | None:
    """Return an expense by its ID."""

    for expense in expenses:
        if expense.id == expense_id:
            return expense

    return None


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
            logger.info(
                "Deleted expense %d",
                expense_id,
            )
            return deleted_expense

    return None


def update_expense(
    expense_id: int,
    name: str | None = None,
    category: ExpenseCategory | None = None,
    amount: Decimal | None = None,
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
            logger.info(
                "Updated expense %d",
                expense_id,
            )
            return expense

    return None


def get_total() -> Decimal:
    """Return the total amount of all recorded expenses."""
    return sum(
        (expense.amount for expense in expenses),
        start=Decimal("0"),
    )
