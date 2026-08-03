import json
import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.core.money import money_from_json, money_to_json
from src.financial.history.models import (
    FinancialSnapshotRecord,
)

logger = get_logger(__name__)


def _encode_category_totals(category_totals: dict) -> str:
    """Serialize a flat category->Decimal dict for storage."""
    return json.dumps(
        {category: money_to_json(amount) for category, amount in category_totals.items()}
    )


def _decode_category_totals(raw: str) -> dict:
    """Restore a flat category->Decimal dict from storage."""
    return {
        category: money_from_json(str(amount))
        for category, amount in json.loads(raw).items()
    }


def load_history_from_file(
    user_id: int,
    db_path: Path = DB_PATH,
) -> list[FinancialSnapshotRecord]:
    """Load a user's historical financial snapshots from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                """
                SELECT timestamp, total_income, total_expenses, net_cash_flow,
                       total_account_balance, total_goal_progress, total_debt,
                       net_worth, health_score, health_status
                FROM financial_history WHERE user_id = ? ORDER BY id
                """,
                (user_id,),
            ).fetchall()
            category_rows = connection.execute(
                "SELECT timestamp, data FROM financial_history_category_totals WHERE user_id = ?",
                (user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load history from {db_path}") from error

    category_totals_by_timestamp = {
        row["timestamp"]: _decode_category_totals(row["data"]) for row in category_rows
    }

    history = []
    for row in rows:
        record = FinancialSnapshotRecord.from_dict(dict(row))
        record.category_totals = category_totals_by_timestamp.get(
            record.timestamp.isoformat(), {}
        )
        history.append(record)

    logger.debug(
        "Loaded %d snapshot(s) for user %d from %s",
        len(history),
        user_id,
        db_path,
    )

    return history


def save_history_to_file(
    history: list[FinancialSnapshotRecord],
    user_id: int,
    db_path: Path = DB_PATH,
) -> None:
    """Save a user's historical snapshots to the database, replacing their existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM financial_history WHERE user_id = ?", (user_id,))
            connection.executemany(
                """
                INSERT INTO financial_history (
                    timestamp, total_income, total_expenses, net_cash_flow,
                    total_account_balance, total_goal_progress, total_debt,
                    net_worth, health_score, health_status, user_id
                )
                VALUES (
                    :timestamp, :total_income, :total_expenses, :net_cash_flow,
                    :total_account_balance, :total_goal_progress, :total_debt,
                    :net_worth, :health_score, :health_status, :user_id
                )
                """,
                [{**record.to_dict(), "user_id": user_id} for record in history],
            )
            connection.execute(
                "DELETE FROM financial_history_category_totals WHERE user_id = ?", (user_id,)
            )
            connection.executemany(
                """
                INSERT INTO financial_history_category_totals (timestamp, data, user_id)
                VALUES (:timestamp, :data, :user_id)
                """,
                [
                    {
                        "timestamp": record.timestamp.isoformat(),
                        "data": _encode_category_totals(record.category_totals),
                        "user_id": user_id,
                    }
                    for record in history
                ],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save history to {db_path}") from error

    logger.debug(
        "Saved %d snapshot(s) for user %d to %s",
        len(history),
        user_id,
        db_path,
    )
