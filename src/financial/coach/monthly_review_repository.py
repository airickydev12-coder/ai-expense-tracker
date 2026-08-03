import json
import sqlite3
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger

logger = get_logger(__name__)


class _DecimalEncoder(json.JSONEncoder):
    """
    Serialize Decimal values found anywhere in a saved monthly review.

    Reviews contain Decimal fields (income_change, expense_change, etc.) at
    arbitrary depth inside nested sections, the same shape of problem
    scenario_workspace already solves -- reusing its tagged-object pattern
    so a matching object_hook can restore Decimal on load without needing
    to know which keys are monetary.
    """

    def default(self, o: object) -> Any:
        if isinstance(o, Decimal):
            return {"__decimal__": str(o)}

        return super().default(o)


def _decimal_object_hook(data: dict) -> object:
    """Restore Decimal values tagged by _DecimalEncoder."""
    if set(data.keys()) == {"__decimal__"}:
        return Decimal(data["__decimal__"])

    return data


def load_monthly_review_history_from_file(
    user_id: int,
    db_path: Path = DB_PATH,
) -> list[dict]:
    """Load a user's saved monthly reviews from the database, oldest first."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT data FROM monthly_review_history WHERE user_id = ? ORDER BY id",
                (user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to load monthly review history from {db_path}"
        ) from error

    try:
        reviews = [
            json.loads(row["data"], object_hook=_decimal_object_hook) for row in rows
        ]
    except json.JSONDecodeError as error:
        raise PersistenceError("Monthly review history contains invalid JSON.") from error

    logger.debug(
        "Loaded %d monthly review(s) for user %d from %s",
        len(reviews),
        user_id,
        db_path,
    )

    return reviews


def save_monthly_review_history_to_file(
    reviews: list[dict],
    user_id: int,
    db_path: Path = DB_PATH,
) -> None:
    """Save a user's monthly reviews to the database, replacing their existing rows."""
    records = [
        {
            "generated_at": review["generated_at"],
            "period_start": review["period_start"],
            "period_end": review["period_end"],
            "data": json.dumps(review, cls=_DecimalEncoder),
            "user_id": user_id,
        }
        for review in reviews
    ]

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "DELETE FROM monthly_review_history WHERE user_id = ?", (user_id,)
            )
            connection.executemany(
                """
                INSERT INTO monthly_review_history (
                    generated_at, period_start, period_end, data, user_id
                )
                VALUES (:generated_at, :period_start, :period_end, :data, :user_id)
                """,
                records,
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to save monthly review history to {db_path}"
        ) from error

    logger.debug(
        "Saved %d monthly review(s) for user %d to %s",
        len(reviews),
        user_id,
        db_path,
    )
