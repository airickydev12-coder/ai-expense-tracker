import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.bills.models import Bill

logger = get_logger(__name__)


def load_bills_from_file(
    user_id: int,
    db_path: Path = DB_PATH,
) -> list[Bill]:
    """Load a user's bills from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT id, name, amount, due_day, is_paid FROM bills WHERE user_id = ? ORDER BY id",
                (user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load bills from {db_path}") from error

    bills = [Bill.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d bill(s) for user %d from %s",
        len(bills),
        user_id,
        db_path,
    )

    return bills


def save_bills_to_file(
    bills: list[Bill],
    user_id: int,
    db_path: Path = DB_PATH,
) -> None:
    """Save a user's bills to the database, replacing their existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM bills WHERE user_id = ?", (user_id,))
            connection.executemany(
                """
                INSERT INTO bills (id, name, amount, due_day, is_paid, user_id)
                VALUES (:id, :name, :amount, :due_day, :is_paid, :user_id)
                """,
                [{**bill.to_dict(), "user_id": user_id} for bill in bills],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save bills to {db_path}") from error

    logger.debug(
        "Saved %d bill(s) for user %d to %s",
        len(bills),
        user_id,
        db_path,
    )
