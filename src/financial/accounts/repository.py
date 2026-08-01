import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.accounts.models import Account

logger = get_logger(__name__)


def load_accounts_from_file(
    db_path: Path = DB_PATH,
) -> list[Account]:
    """Load accounts from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT id, name, account_type, balance FROM accounts ORDER BY id"
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load accounts from {db_path}") from error

    accounts = [Account.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d account(s) from %s",
        len(accounts),
        db_path,
    )

    return accounts


def save_accounts_to_file(
    accounts: list[Account],
    db_path: Path = DB_PATH,
) -> None:
    """Save accounts to the database, replacing all existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM accounts")
            connection.executemany(
                """
                INSERT INTO accounts (id, name, account_type, balance)
                VALUES (:id, :name, :account_type, :balance)
                """,
                [account.to_dict() for account in accounts],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save accounts to {db_path}") from error

    logger.debug(
        "Saved %d account(s) to %s",
        len(accounts),
        db_path,
    )
