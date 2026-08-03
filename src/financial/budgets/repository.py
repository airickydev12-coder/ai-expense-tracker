import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.budgets.models import Budget

logger = get_logger(__name__)


def load_budgets_from_file(
    user_id: int,
    db_path: Path = DB_PATH,
) -> list[Budget]:
    """Load a user's budgets from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                'SELECT category, "limit" FROM budgets WHERE user_id = ? ORDER BY category',
                (user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load budgets from {db_path}") from error

    budgets = [Budget.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d budget(s) for user %d from %s",
        len(budgets),
        user_id,
        db_path,
    )

    return budgets


def save_budgets_to_file(
    budgets: list[Budget],
    user_id: int,
    db_path: Path = DB_PATH,
) -> None:
    """Save a user's budgets to the database, replacing their existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM budgets WHERE user_id = ?", (user_id,))
            connection.executemany(
                'INSERT INTO budgets (category, "limit", user_id) VALUES (:category, :limit, :user_id)',
                [{**budget.to_dict(), "user_id": user_id} for budget in budgets],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save budgets to {db_path}") from error

    logger.debug(
        "Saved %d budget(s) for user %d to %s",
        len(budgets),
        user_id,
        db_path,
    )
