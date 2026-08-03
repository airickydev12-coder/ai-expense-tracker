import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.notifications.models import NotificationLogEntry

logger = get_logger(__name__)


def load_notification_log_from_file(
    user_id: int,
    db_path: Path = DB_PATH,
) -> list[NotificationLogEntry]:
    """Load a user's notification log from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                """
                SELECT id, notification_key, channel, subject, body, sent_at, status
                FROM notification_log WHERE user_id = ? ORDER BY id
                """,
                (user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load notification log from {db_path}") from error

    entries = [NotificationLogEntry.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d notification log entr(y/ies) for user %d from %s",
        len(entries),
        user_id,
        db_path,
    )

    return entries


def save_notification_log_to_file(
    entries: list[NotificationLogEntry],
    user_id: int,
    db_path: Path = DB_PATH,
) -> None:
    """Save a user's notification log to the database, replacing their existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM notification_log WHERE user_id = ?", (user_id,))
            connection.executemany(
                """
                INSERT INTO notification_log
                    (id, notification_key, channel, subject, body, sent_at, status, user_id)
                VALUES
                    (:id, :notification_key, :channel, :subject, :body, :sent_at, :status, :user_id)
                """,
                [{**entry.to_dict(), "user_id": user_id} for entry in entries],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save notification log to {db_path}") from error

    logger.debug(
        "Saved %d notification log entr(y/ies) for user %d to %s",
        len(entries),
        user_id,
        db_path,
    )
