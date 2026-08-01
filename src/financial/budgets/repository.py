import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.budgets.models import Budget

logger = get_logger(__name__)


def load_budgets_from_file(
    db_path: Path = DB_PATH,
) -> list[Budget]:
    """Load budgets from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                'SELECT category, "limit" FROM budgets ORDER BY category'
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load budgets from {db_path}") from error

    budgets = [Budget.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d budget(s) from %s",
        len(budgets),
        db_path,
    )

    return budgets


def save_budgets_to_file(
    budgets: list[Budget],
    db_path: Path = DB_PATH,
) -> None:
    """Save budgets to the database, replacing all existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM budgets")
            connection.executemany(
                'INSERT INTO budgets (category, "limit") VALUES (:category, :limit)',
                [budget.to_dict() for budget in budgets],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save budgets to {db_path}") from error

    logger.debug(
        "Saved %d budget(s) to %s",
        len(budgets),
        db_path,
    )
