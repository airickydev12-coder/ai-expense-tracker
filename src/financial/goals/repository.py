import json
from pathlib import Path

from src.core.config import DATA_DIR
from src.financial.goals.models import Goal


GOALS_FILE = DATA_DIR / "goals.json"


def load_goals_from_file(
    file_path: Path = GOALS_FILE,
) -> list[Goal]:
    """Load goals from a JSON file."""
    if not file_path.exists():
        return []

    try:
        with file_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Goal data file contains invalid JSON: {file_path}"
        ) from error

    if not isinstance(raw_data, list):
        raise ValueError("Goal data must be stored as a JSON list.")

    return [
        Goal.from_dict(goal_data)
        for goal_data in raw_data
    ]


def save_goals_to_file(
    goals: list[Goal],
    file_path: Path = GOALS_FILE,
) -> None:
    """Save goals to a JSON file."""
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    goal_data = [
        goal.to_dict()
        for goal in goals
    ]

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            goal_data,
            file,
            indent=4,
        )