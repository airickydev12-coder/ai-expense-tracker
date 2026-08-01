"""Application services for financial goals."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import TypeAlias

from src.core.config import DB_PATH
from src.core.exceptions import ValidationError
from src.core.logging import get_logger
from src.core.money import (
    ZERO,
    to_money,
)
from src.financial.goal_ledger.service import (
    migrate_existing_goal_balances,
    record_contribution,
)
from src.financial.goals.models import Goal
from src.financial.goals.repository import (
    load_goals_from_file,
    save_goals_to_file,
)
from src.financial.planning.repository import (
    remove_goal_planning_request_from_file,
)

logger = get_logger(__name__)

MoneyInput: TypeAlias = Decimal | int | float | str

goals: list[Goal] = []


def load_goals(
    file_path: Path = DB_PATH,
    ledger_file_path: Path | None = None,
) -> None:
    """Load goals and migrate existing balances."""
    resolved_ledger_path = _resolve_ledger_file_path(
        goals_file_path=file_path,
        ledger_file_path=ledger_file_path,
    )

    goals.clear()
    goals.extend(load_goals_from_file(file_path))

    migrate_existing_goal_balances(
        goals,
        ledger_file_path=resolved_ledger_path,
    )


def save_goals(
    file_path: Path = DB_PATH,
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

    return max(goal.id for goal in goals) + 1


def add_goal(
    name: str,
    target_amount: MoneyInput,
    current_amount: MoneyInput = ZERO,
    file_path: Path = DB_PATH,
    ledger_file_path: Path | None = None,
) -> Goal:
    """Create and save a financial goal."""
    resolved_ledger_path = _resolve_ledger_file_path(
        goals_file_path=file_path,
        ledger_file_path=ledger_file_path,
    )

    normalized_target = to_money(target_amount)
    normalized_current = to_money(current_amount)

    goal = Goal(
        id=get_next_goal_id(),
        name=name,
        target_amount=normalized_target,
        current_amount=normalized_current,
    )

    goals.append(goal)
    save_goals(file_path)

    if normalized_current > ZERO:
        migrate_existing_goal_balances(
            [goal],
            ledger_file_path=resolved_ledger_path,
        )

    logger.info(
        "Added goal %d (%s)",
        goal.id,
        goal.name,
    )

    return goal


def update_goal(
    goal_id: int,
    name: str | None = None,
    target_amount: MoneyInput | None = None,
    current_amount: MoneyInput | None = None,
    file_path: Path = DB_PATH,
) -> Goal | None:
    """
    Update an existing goal.

    Direct cached-balance changes remain temporarily available
    for backward compatibility. New contributions must use the
    append-only goal ledger.
    """
    goal = get_goal_by_id(goal_id)

    if goal is None:
        return None

    normalized_target = (
        to_money(target_amount) if target_amount is not None else goal.target_amount
    )

    normalized_current = (
        to_money(current_amount) if current_amount is not None else goal.current_amount
    )

    updated_goal = Goal(
        id=goal.id,
        name=(name.strip() if name is not None else goal.name),
        target_amount=normalized_target,
        current_amount=normalized_current,
    )

    goal_index = goals.index(goal)
    goals[goal_index] = updated_goal

    save_goals(file_path)

    logger.info(
        "Updated goal %d",
        goal_id,
    )

    return updated_goal


def contribute_to_goal(
    goal_id: int,
    contribution: MoneyInput,
    file_path: Path = DB_PATH,
    ledger_file_path: Path | None = None,
    effective_date: date | None = None,
    source: str = "MANUAL",
    note: str = "",
    correlation_id: str | None = None,
) -> Goal | None:
    """Record a contribution through the goal ledger."""
    normalized_contribution = to_money(contribution)

    if normalized_contribution < ZERO:
        raise ValidationError("Goal contribution cannot be negative.")

    goal = get_goal_by_id(goal_id)

    if goal is None:
        return None

    resolved_ledger_path = _resolve_ledger_file_path(
        goals_file_path=file_path,
        ledger_file_path=ledger_file_path,
    )

    record_contribution(
        goal,
        normalized_contribution,
        goals=goals,
        effective_date=effective_date,
        source=source,
        note=note,
        correlation_id=correlation_id,
        ledger_file_path=resolved_ledger_path,
        goals_file_path=file_path,
    )

    logger.info(
        "Recorded contribution of %s to goal %d",
        normalized_contribution,
        goal_id,
    )

    return get_goal_by_id(goal_id)


def delete_goal(
    goal_id: int,
    file_path: Path = DB_PATH,
) -> Goal | None:
    """
    Delete a goal from the active goal list.

    Ledger entries remain preserved as an audit trail.
    """
    for index, goal in enumerate(goals):
        if goal.id != goal_id:
            continue

        deleted_goal = goals.pop(index)
        save_goals(file_path)

        remove_goal_planning_request_from_file(
            goal_id,
            file_path=file_path,
        )

        logger.info(
            "Deleted goal %d",
            goal_id,
        )

        return deleted_goal

    return None


def _resolve_ledger_file_path(
    *,
    goals_file_path: Path,
    ledger_file_path: Path | None,
) -> Path:
    """
    Resolve the ledger associated with a goals repository.

    The ledger and goals now share the same SQLite database, so an
    alternate goals path (e.g. an isolated test database) implies the
    same alternate ledger path unless explicitly overridden.
    """
    if ledger_file_path is not None:
        return ledger_file_path

    return goals_file_path
