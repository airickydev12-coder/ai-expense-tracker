import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.recommendations.history import RecommendationRecord

logger = get_logger(__name__)


def load_recommendation_history_from_file(
    db_path: Path = DB_PATH,
) -> list[RecommendationRecord]:
    """Load recommendation lifecycle records from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute("""
                SELECT recommendation_key, status, created_at, updated_at, note
                FROM recommendation_history ORDER BY recommendation_key
                """).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to load recommendation history from {db_path}"
        ) from error

    records = [RecommendationRecord.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d recommendation history record(s) from %s",
        len(records),
        db_path,
    )

    return records


def save_recommendation_history_to_file(
    records: list[RecommendationRecord],
    db_path: Path = DB_PATH,
) -> None:
    """Save recommendation lifecycle records, replacing all existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM recommendation_history")
            connection.executemany(
                """
                INSERT INTO recommendation_history (
                    recommendation_key, status, created_at, updated_at, note
                )
                VALUES (:recommendation_key, :status, :created_at, :updated_at, :note)
                """,
                [record.to_dict() for record in records],
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to save recommendation history to {db_path}"
        ) from error

    logger.debug(
        "Saved %d recommendation history record(s) to %s",
        len(records),
        db_path,
    )
