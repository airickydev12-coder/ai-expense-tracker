import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.accounts.models import Account

logger = get_logger(__name__)


def load_accounts_from_file(
    user_id: int,
    db_path: Path = DB_PATH,
) -> list[Account]:
    """Load a user's accounts from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT id, name, account_type, balance FROM accounts WHERE user_id = ? ORDER BY id",
                (user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load accounts from {db_path}") from error

    accounts = [Account.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d account(s) for user %d from %s",
        len(accounts),
        user_id,
        db_path,
    )

    return accounts


def save_accounts_to_file(
    accounts: list[Account],
    user_id: int,
    db_path: Path = DB_PATH,
) -> None:
    """Save a user's accounts to the database, replacing their existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM accounts WHERE user_id = ?", (user_id,))
            connection.executemany(
                """
                INSERT INTO accounts (id, name, account_type, balance, user_id)
                VALUES (:id, :name, :account_type, :balance, :user_id)
                """,
                [{**account.to_dict(), "user_id": user_id} for account in accounts],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save accounts to {db_path}") from error

    logger.debug(
        "Saved %d account(s) for user %d to %s",
        len(accounts),
        user_id,
        db_path,
    )
