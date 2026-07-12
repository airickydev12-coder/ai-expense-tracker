from pathlib import Path

from src.financial.goals.models import Goal
from src.financial.goals.repository import (
    GOALS_FILE,
    load_goals_from_file,
    save_goals_to_file,
)


goals: list[Goal] = []


def load_goals(
    file_path: Path = GOALS_FILE,
) -> None:
    """Load goals into application memory."""
    goals.clear()
    goals.extend(
        load_goals_from_file(file_path)
    )


def save_goals(
    file_path: Path = GOALS_FILE,
) -> None:
    """Save all goals from application memory."""
    save_goals_to_file(
        goals,
        file_path,
    )


def get_goals() -> list[Goal]:
    """Return a copy of all goals."""
    return goals.copy()


def get_goal_by_id(
    goal_id: int,
) -> Goal | None:
    """Return a goal by ID."""
    for goal in goals:
        if goal.id == goal_id:
            return goal

    return None


def get_next_goal_id() -> int:
    """Return the next available goal ID."""
    if not goals:
        return 1

    return max(
        goal.id
        for goal in goals
    ) + 1


def add_goal(
    name: str,
    target_amount: float,
    current_amount: float = 0,
    file_path: Path = GOALS_FILE,
) -> Goal:
    """Create and save a financial goal."""
    goal = Goal(
        id=get_next_goal_id(),
        name=name,
        target_amount=target_amount,
        current_amount=current_amount,
    )

    goals.append(goal)
    save_goals(file_path)

    return goal


def update_goal(
    goal_id: int,
    name: str | None = None,
    target_amount: float | None = None,
    current_amount: float | None = None,
    file_path: Path = GOALS_FILE,
) -> Goal | None:
    """Update an existing financial goal."""
    goal = get_goal_by_id(goal_id)

    if goal is None:
        return None

    updated_goal = Goal(
        id=goal.id,
        name=(
            name.strip()
            if name is not None
            else goal.name
        ),
        target_amount=(
            target_amount
            if target_amount is not None
            else goal.target_amount
        ),
        current_amount=(
            current_amount
            if current_amount is not None
            else goal.current_amount
        ),
    )

    goal_index = goals.index(goal)
    goals[goal_index] = updated_goal

    save_goals(file_path)

    return updated_goal


def contribute_to_goal(
    goal_id: int,
    contribution: float,
    file_path: Path = GOALS_FILE,
) -> Goal | None:
    """Apply a contribution to an existing goal."""
    if contribution < 0:
        raise ValueError("Goal contribution cannot be negative.")

    goal = get_goal_by_id(goal_id)

    if goal is None:
        return None

    updated_amount = min(
        goal.current_amount + contribution,
        goal.target_amount,
    )

    return update_goal(
        goal_id=goal.id,
        current_amount=updated_amount,
        file_path=file_path,
    )


def delete_goal(
    goal_id: int,
    file_path: Path = GOALS_FILE,
) -> Goal | None:
    """Delete a goal by ID."""
    for index, goal in enumerate(goals):
        if goal.id == goal_id:
            deleted_goal = goals.pop(index)
            save_goals(file_path)
            return deleted_goal

    return None