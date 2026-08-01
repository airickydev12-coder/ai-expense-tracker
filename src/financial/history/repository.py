import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.history.models import (
    FinancialSnapshotRecord,
)

logger = get_logger(__name__)


def load_history_from_file(
    db_path: Path = DB_PATH,
) -> list[FinancialSnapshotRecord]:
    """Load historical financial snapshots from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute("""
                SELECT timestamp, total_income, total_expenses, net_cash_flow,
                       total_account_balance, total_goal_progress, total_debt,
                       net_worth, health_score, health_status
                FROM financial_history ORDER BY id
                """).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load history from {db_path}") from error

    history = [FinancialSnapshotRecord.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d snapshot(s) from %s",
        len(history),
        db_path,
    )

    return history


def save_history_to_file(
    history: list[FinancialSnapshotRecord],
    db_path: Path = DB_PATH,
) -> None:
    """Save historical snapshots to the database, replacing all existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM financial_history")
            connection.executemany(
                """
                INSERT INTO financial_history (
                    timestamp, total_income, total_expenses, net_cash_flow,
                    total_account_balance, total_goal_progress, total_debt,
                    net_worth, health_score, health_status
                )
                VALUES (
                    :timestamp, :total_income, :total_expenses, :net_cash_flow,
                    :total_account_balance, :total_goal_progress, :total_debt,
                    :net_worth, :health_score, :health_status
                )
                """,
                [record.to_dict() for record in history],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save history to {db_path}") from error

    logger.debug(
        "Saved %d snapshot(s) to %s",
        len(history),
        db_path,
    )
