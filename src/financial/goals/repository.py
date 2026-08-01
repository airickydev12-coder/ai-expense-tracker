import json
from pathlib import Path

from src.core.config import GOALS_FILE
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.goals.models import Goal

logger = get_logger(__name__)


def load_goals_from_file(
    file_path: Path = GOALS_FILE,
) -> list[Goal]:
    """Load goals from a JSON file."""
    if not file_path.exists():
        return []

    try:
        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            raw_data = json.load(file)

    except json.JSONDecodeError as error:
        logger.error(
            "Failed to parse goals file %s: %s",
            file_path,
            error,
        )
        raise PersistenceError(
            f"Goal data file contains invalid JSON: {file_path}"
        ) from error

    if not isinstance(raw_data, list):
        raise PersistenceError("Goal data must be stored as a JSON list.")

    goals = [Goal.from_dict(goal_data) for goal_data in raw_data]

    logger.debug(
        "Loaded %d goal(s) from %s",
        len(goals),
        file_path,
    )

    return goals


def save_goals_to_file(
    goals: list[Goal],
    file_path: Path = GOALS_FILE,
) -> None:
    """Atomically save goals to disk."""
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    goal_data = [goal.to_dict() for goal in goals]

    temporary_path = file_path.with_suffix(file_path.suffix + ".tmp")

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                goal_data,
                file,
                indent=4,
            )

        temporary_path.replace(file_path)

    except OSError:
        temporary_path.unlink(
            missing_ok=True,
        )
        raise

    logger.debug(
        "Saved %d goal(s) to %s",
        len(goals),
        file_path,
    )
