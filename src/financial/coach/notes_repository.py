import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger

logger = get_logger(__name__)


def load_notes_from_file(
    user_id: int,
    db_path: Path = DB_PATH,
) -> list[dict]:
    """Load a user's saved notes from the database, oldest first."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT id, created_at, title, content FROM saved_notes WHERE user_id = ? ORDER BY id",
                (user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load notes from {db_path}") from error

    notes = [dict(row) for row in rows]

    logger.debug(
        "Loaded %d note(s) for user %d from %s",
        len(notes),
        user_id,
        db_path,
    )

    return notes


def save_notes_to_file(
    notes: list[dict],
    user_id: int,
    db_path: Path = DB_PATH,
) -> None:
    """Save a user's notes to the database, replacing their existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM saved_notes WHERE user_id = ?", (user_id,))
            connection.executemany(
                """
                INSERT INTO saved_notes (id, created_at, title, content, user_id)
                VALUES (:id, :created_at, :title, :content, :user_id)
                """,
                [{**note, "user_id": user_id} for note in notes],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save notes to {db_path}") from error

    logger.debug(
        "Saved %d note(s) for user %d to %s",
        len(notes),
        user_id,
        db_path,
    )
