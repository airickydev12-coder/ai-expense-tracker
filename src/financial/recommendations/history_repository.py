import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.recommendations.history import RecommendationRecord

logger = get_logger(__name__)


def load_recommendation_history_from_file(
    user_id: int,
    db_path: Path = DB_PATH,
) -> list[RecommendationRecord]:
    """Load a user's recommendation lifecycle records from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                """
                SELECT recommendation_key, status, created_at, updated_at, note
                FROM recommendation_history WHERE user_id = ? ORDER BY recommendation_key
                """,
                (user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to load recommendation history from {db_path}"
        ) from error

    records = [RecommendationRecord.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d recommendation history record(s) for user %d from %s",
        len(records),
        user_id,
        db_path,
    )

    return records


def save_recommendation_history_to_file(
    records: list[RecommendationRecord],
    user_id: int,
    db_path: Path = DB_PATH,
) -> None:
    """Save a user's recommendation lifecycle records, replacing their existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "DELETE FROM recommendation_history WHERE user_id = ?", (user_id,)
            )
            connection.executemany(
                """
                INSERT INTO recommendation_history (
                    recommendation_key, status, created_at, updated_at, note, user_id
                )
                VALUES (:recommendation_key, :status, :created_at, :updated_at, :note, :user_id)
                """,
                [{**record.to_dict(), "user_id": user_id} for record in records],
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to save recommendation history to {db_path}"
        ) from error

    logger.debug(
        "Saved %d recommendation history record(s) for user %d to %s",
        len(records),
        user_id,
        db_path,
    )
