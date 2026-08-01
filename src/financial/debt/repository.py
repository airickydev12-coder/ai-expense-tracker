import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.debt.models import Debt

logger = get_logger(__name__)


def load_debts_from_file(
    db_path: Path = DB_PATH,
) -> list[Debt]:
    """Load debts from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute("""
                SELECT id, name, balance, interest_rate, minimum_payment
                FROM debts ORDER BY id
                """).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load debts from {db_path}") from error

    debts = [Debt.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d debt(s) from %s",
        len(debts),
        db_path,
    )

    return debts


def save_debts_to_file(
    debts: list[Debt],
    db_path: Path = DB_PATH,
) -> None:
    """Save debts to the database, replacing all existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM debts")
            connection.executemany(
                """
                INSERT INTO debts (id, name, balance, interest_rate, minimum_payment)
                VALUES (:id, :name, :balance, :interest_rate, :minimum_payment)
                """,
                [debt.to_dict() for debt in debts],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save debts to {db_path}") from error

    logger.debug(
        "Saved %d debt(s) to %s",
        len(debts),
        db_path,
    )
