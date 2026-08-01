import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.expenses.models import Expense

logger = get_logger(__name__)


def load_expenses_from_file(
    db_path: Path = DB_PATH,
) -> list[Expense]:
    """Load expenses from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT id, name, category, amount FROM expenses ORDER BY id"
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load expenses from {db_path}") from error

    expenses = [Expense.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d expense(s) from %s",
        len(expenses),
        db_path,
    )

    return expenses


def save_expenses_to_file(
    expenses: list[Expense],
    db_path: Path = DB_PATH,
) -> None:
    """Save expenses to the database, replacing all existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM expenses")
            connection.executemany(
                """
                INSERT INTO expenses (id, name, category, amount)
                VALUES (:id, :name, :category, :amount)
                """,
                [expense.to_dict() for expense in expenses],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save expenses to {db_path}") from error

    logger.debug(
        "Saved %d expense(s) to %s",
        len(expenses),
        db_path,
    )
