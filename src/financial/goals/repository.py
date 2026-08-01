import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.goals.models import Goal

logger = get_logger(__name__)


def load_goals_from_file(
    db_path: Path = DB_PATH,
) -> list[Goal]:
    """Load goals from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT id, name, target_amount, current_amount FROM goals ORDER BY id"
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load goals from {db_path}") from error

    goals = [Goal.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d goal(s) from %s",
        len(goals),
        db_path,
    )

    return goals


def save_goals_to_file(
    goals: list[Goal],
    db_path: Path = DB_PATH,
) -> None:
    """Save goals to the database, replacing all existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM goals")
            connection.executemany(
                """
                INSERT INTO goals (id, name, target_amount, current_amount)
                VALUES (:id, :name, :target_amount, :current_amount)
                """,
                [goal.to_dict() for goal in goals],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save goals to {db_path}") from error

    logger.debug(
        "Saved %d goal(s) to %s",
        len(goals),
        db_path,
    )
