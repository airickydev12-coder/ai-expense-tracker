import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.bills.models import Bill

logger = get_logger(__name__)


def load_bills_from_file(
    db_path: Path = DB_PATH,
) -> list[Bill]:
    """Load bills from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT id, name, amount, due_day, is_paid FROM bills ORDER BY id"
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load bills from {db_path}") from error

    bills = [Bill.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d bill(s) from %s",
        len(bills),
        db_path,
    )

    return bills


def save_bills_to_file(
    bills: list[Bill],
    db_path: Path = DB_PATH,
) -> None:
    """Save bills to the database, replacing all existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM bills")
            connection.executemany(
                """
                INSERT INTO bills (id, name, amount, due_day, is_paid)
                VALUES (:id, :name, :amount, :due_day, :is_paid)
                """,
                [bill.to_dict() for bill in bills],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save bills to {db_path}") from error

    logger.debug(
        "Saved %d bill(s) to %s",
        len(bills),
        db_path,
    )
