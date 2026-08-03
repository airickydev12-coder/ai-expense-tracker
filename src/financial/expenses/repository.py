import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.expenses.models import Expense

logger = get_logger(__name__)


def load_expenses_from_file(
    user_id: int,
    db_path: Path = DB_PATH,
) -> list[Expense]:
    """Load a user's expenses from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT id, name, category, amount FROM expenses WHERE user_id = ? ORDER BY id",
                (user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load expenses from {db_path}") from error

    expenses = [Expense.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d expense(s) for user %d from %s",
        len(expenses),
        user_id,
        db_path,
    )

    return expenses


def save_expenses_to_file(
    expenses: list[Expense],
    user_id: int,
    db_path: Path = DB_PATH,
) -> None:
    """Save a user's expenses to the database, replacing their existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
            connection.executemany(
                """
                INSERT INTO expenses (id, name, category, amount, user_id)
                VALUES (:id, :name, :category, :amount, :user_id)
                """,
                [{**expense.to_dict(), "user_id": user_id} for expense in expenses],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save expenses to {db_path}") from error

    logger.debug(
        "Saved %d expense(s) for user %d to %s",
        len(expenses),
        user_id,
        db_path,
    )
