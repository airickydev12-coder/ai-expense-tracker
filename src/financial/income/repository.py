import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.income.models import Income

logger = get_logger(__name__)


def load_income_from_file(
    db_path: Path = DB_PATH,
) -> list[Income]:
    """Load income entries from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT id, source, amount FROM income ORDER BY id"
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load income from {db_path}") from error

    income_entries = [Income.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d income entry(ies) from %s",
        len(income_entries),
        db_path,
    )

    return income_entries


def save_income_to_file(
    income_entries: list[Income],
    db_path: Path = DB_PATH,
) -> None:
    """Save income entries to the database, replacing all existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM income")
            connection.executemany(
                """
                INSERT INTO income (id, source, amount)
                VALUES (:id, :source, :amount)
                """,
                [income.to_dict() for income in income_entries],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save income to {db_path}") from error

    logger.debug(
        "Saved %d income entry(ies) to %s",
        len(income_entries),
        db_path,
    )
