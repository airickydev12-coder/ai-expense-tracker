import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.goals.models import Goal

logger = get_logger(__name__)


def load_goals_from_file(
    user_id: int,
    db_path: Path = DB_PATH,
) -> list[Goal]:
    """Load a user's goals from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT id, name, target_amount, current_amount FROM goals "
                "WHERE user_id = ? ORDER BY id",
                (user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load goals from {db_path}") from error

    goals = [Goal.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d goal(s) for user %d from %s",
        len(goals),
        user_id,
        db_path,
    )

    return goals


def save_goals_to_file(
    goals: list[Goal],
    user_id: int,
    db_path: Path = DB_PATH,
) -> None:
    """Save a user's goals to the database, replacing their existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
            connection.executemany(
                """
                INSERT INTO goals (id, name, target_amount, current_amount, user_id)
                VALUES (:id, :name, :target_amount, :current_amount, :user_id)
                """,
                [{**goal.to_dict(), "user_id": user_id} for goal in goals],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save goals to {db_path}") from error

    logger.debug(
        "Saved %d goal(s) for user %d to %s",
        len(goals),
        user_id,
        db_path,
    )
