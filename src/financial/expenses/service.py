from decimal import Decimal
from pathlib import Path

from src.core.config import DB_PATH
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

expenses: dict[int, list[Expense]] = {}


def _ensure_loaded(user_id: int, db_path: Path = DB_PATH) -> None:
    """Lazily load a user's expenses into the cache on first access."""
    if user_id not in expenses:
        expenses[user_id] = load_expenses_from_file(user_id, db_path)


def load_expenses(user_id: int, db_path: Path = DB_PATH) -> None:
    """Force-reload a user's expenses from the repository."""
    expenses[user_id] = load_expenses_from_file(user_id, db_path)


def save_expenses(user_id: int, db_path: Path = DB_PATH) -> None:
    """Save a user's expenses using the repository."""
    save_expenses_to_file(expenses[user_id], user_id, db_path)


def get_next_expense_id(user_id: int) -> int:
    """Return the next available expense ID for this user."""
    user_expenses = expenses.get(user_id, [])
    if not user_expenses:
        return 1

    return max(expense.id for expense in user_expenses) + 1


def add_expense(
    user_id: int,
    name: str,
    category: ExpenseCategory,
    amount: Decimal,
    db_path: Path = DB_PATH,
) -> Expense:
    """Create and add a new expense for this user."""
    _ensure_loaded(user_id, db_path)

    expense = Expense(
        id=get_next_expense_id(user_id),
        name=name,
        category=category,
        amount=amount,
    )

    expenses[user_id].append(expense)
    save_expenses(user_id, db_path)

    event_bus.publish(FinancialEvent.EXPENSE_ADDED, expense)

    logger.info(
        "Added expense %d (%s, %s) for user %d",
        expense.id,
        expense.name,
        expense.category.value,
        user_id,
    )

    return expense


def get_expenses(user_id: int, db_path: Path = DB_PATH) -> list[Expense]:
    """Return a copy of all of this user's recorded expenses."""
    _ensure_loaded(user_id, db_path)
    return expenses[user_id].copy()


def get_expense_by_id(
    user_id: int,
    expense_id: int,
    db_path: Path = DB_PATH,
) -> Expense | None:
    """Return one of this user's expenses by its ID."""
    _ensure_loaded(user_id, db_path)

    for expense in expenses[user_id]:
        if expense.id == expense_id:
            return expense

    return None


def delete_expense(user_id: int, expense_id: int, db_path: Path = DB_PATH) -> Expense | None:
    """
    Delete one of this user's expenses by ID.

    Args:
        user_id: The owning user's ID.
        expense_id: The ID of the expense to delete.
        db_path: Database path override, mainly for tests.

    Returns:
        Expense | None: The deleted expense, or None if not found.
    """
    _ensure_loaded(user_id, db_path)

    for index, expense in enumerate(expenses[user_id]):
        if expense.id == expense_id:
            deleted_expense = expenses[user_id].pop(index)
            save_expenses(user_id, db_path)
            logger.info(
                "Deleted expense %d for user %d",
                expense_id,
                user_id,
            )
            return deleted_expense

    return None


def update_expense(
    user_id: int,
    expense_id: int,
    name: str | None = None,
    category: ExpenseCategory | None = None,
    amount: Decimal | None = None,
    db_path: Path = DB_PATH,
) -> Expense | None:
    """Update one of this user's existing expenses by ID."""
    _ensure_loaded(user_id, db_path)

    for expense in expenses[user_id]:
        if expense.id == expense_id:
            if name is not None:
                expense.name = name

            if category is not None:
                expense.category = category

            if amount is not None:
                expense.amount = amount

            save_expenses(user_id, db_path)
            logger.info(
                "Updated expense %d for user %d",
                expense_id,
                user_id,
            )
            return expense

    return None


def get_total(user_id: int, db_path: Path = DB_PATH) -> Decimal:
    """Return the total amount of all of this user's recorded expenses."""
    _ensure_loaded(user_id, db_path)
    return sum(
        (expense.amount for expense in expenses[user_id]),
        start=Decimal("0"),
    )
