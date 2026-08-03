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
from src.financial.goal_ledger.models import GoalLedgerEntry
from src.financial.goal_ledger.repository import load_goal_ledger_from_file
from src.financial.goal_ledger.service import (
    migrate_existing_goal_balances,
    reconcile_goal_balance,
    record_adjustment,
    record_contribution,
    record_withdrawal,
    reverse_entry,
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

goals: dict[int, list[Goal]] = {}


def _ensure_loaded(user_id: int, file_path: Path = DB_PATH) -> None:
    """Lazily load a user's goals into the cache on first access."""
    if user_id not in goals:
        load_goals(user_id, file_path)


def load_goals(
    user_id: int,
    file_path: Path = DB_PATH,
    ledger_file_path: Path | None = None,
) -> None:
    """Load a user's goals and migrate existing balances."""
    resolved_ledger_path = _resolve_ledger_file_path(
        goals_file_path=file_path,
        ledger_file_path=ledger_file_path,
    )

    goals[user_id] = load_goals_from_file(user_id, file_path)

    migrate_existing_goal_balances(
        user_id,
        goals[user_id],
        ledger_file_path=resolved_ledger_path,
    )


def save_goals(
    user_id: int,
    file_path: Path = DB_PATH,
) -> None:
    """Save a user's goals from application memory."""
    save_goals_to_file(
        goals[user_id],
        user_id,
        file_path,
    )


def get_goals(user_id: int, file_path: Path = DB_PATH) -> list[Goal]:
    """Return a copy of all of this user's goals."""
    _ensure_loaded(user_id, file_path)
    return goals[user_id].copy()


def get_goal_by_id(
    user_id: int,
    goal_id: int,
    file_path: Path = DB_PATH,
) -> Goal | None:
    """Return one of this user's goals by ID."""
    _ensure_loaded(user_id, file_path)

    for goal in goals[user_id]:
        if goal.id == goal_id:
            return goal

    return None


def get_next_goal_id(user_id: int) -> int:
    """Return the next available goal ID for this user."""
    user_goals = goals.get(user_id, [])
    if not user_goals:
        return 1

    return max(goal.id for goal in user_goals) + 1


def add_goal(
    user_id: int,
    name: str,
    target_amount: MoneyInput,
    current_amount: MoneyInput = ZERO,
    file_path: Path = DB_PATH,
    ledger_file_path: Path | None = None,
) -> Goal:
    """Create and save a financial goal for this user."""
    _ensure_loaded(user_id, file_path)

    resolved_ledger_path = _resolve_ledger_file_path(
        goals_file_path=file_path,
        ledger_file_path=ledger_file_path,
    )

    normalized_target = to_money(target_amount)
    normalized_current = to_money(current_amount)

    goal = Goal(
        id=get_next_goal_id(user_id),
        name=name,
        target_amount=normalized_target,
        current_amount=normalized_current,
    )

    goals[user_id].append(goal)
    save_goals(user_id, file_path)

    if normalized_current > ZERO:
        migrate_existing_goal_balances(
            user_id,
            [goal],
            ledger_file_path=resolved_ledger_path,
        )

    logger.info(
        "Added goal %d (%s) for user %d",
        goal.id,
        goal.name,
        user_id,
    )

    return goal


def update_goal(
    user_id: int,
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
    _ensure_loaded(user_id, file_path)

    goal = get_goal_by_id(user_id, goal_id, file_path)

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

    goal_index = goals[user_id].index(goal)
    goals[user_id][goal_index] = updated_goal

    save_goals(user_id, file_path)

    logger.info(
        "Updated goal %d for user %d",
        goal_id,
        user_id,
    )

    return updated_goal


def contribute_to_goal(
    user_id: int,
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

    _ensure_loaded(user_id, file_path)

    goal = get_goal_by_id(user_id, goal_id, file_path)

    if goal is None:
        return None

    resolved_ledger_path = _resolve_ledger_file_path(
        goals_file_path=file_path,
        ledger_file_path=ledger_file_path,
    )

    record_contribution(
        user_id,
        goal,
        normalized_contribution,
        goals=goals[user_id],
        effective_date=effective_date,
        source=source,
        note=note,
        correlation_id=correlation_id,
        ledger_file_path=resolved_ledger_path,
        goals_file_path=file_path,
    )

    logger.info(
        "Recorded contribution of %s to goal %d for user %d",
        normalized_contribution,
        goal_id,
        user_id,
    )

    return get_goal_by_id(user_id, goal_id, file_path)


def withdraw_from_goal(
    user_id: int,
    goal_id: int,
    amount: MoneyInput,
    file_path: Path = DB_PATH,
    ledger_file_path: Path | None = None,
    effective_date: date | None = None,
    source: str = "MANUAL",
    note: str = "",
    correlation_id: str | None = None,
) -> Goal | None:
    """Record a withdrawal through the goal ledger."""
    _ensure_loaded(user_id, file_path)

    goal = get_goal_by_id(user_id, goal_id, file_path)

    if goal is None:
        return None

    resolved_ledger_path = _resolve_ledger_file_path(
        goals_file_path=file_path,
        ledger_file_path=ledger_file_path,
    )

    record_withdrawal(
        user_id,
        goal,
        to_money(amount),
        goals=goals[user_id],
        effective_date=effective_date,
        source=source,
        note=note,
        correlation_id=correlation_id,
        ledger_file_path=resolved_ledger_path,
        goals_file_path=file_path,
    )

    logger.info(
        "Recorded withdrawal of %s from goal %d for user %d",
        amount,
        goal_id,
        user_id,
    )

    return get_goal_by_id(user_id, goal_id, file_path)


def adjust_goal_balance(
    user_id: int,
    goal_id: int,
    amount: MoneyInput,
    file_path: Path = DB_PATH,
    ledger_file_path: Path | None = None,
    effective_date: date | None = None,
    source: str = "MANUAL",
    note: str = "",
    correlation_id: str | None = None,
) -> Goal | None:
    """Record a signed balance correction through the goal ledger."""
    _ensure_loaded(user_id, file_path)

    goal = get_goal_by_id(user_id, goal_id, file_path)

    if goal is None:
        return None

    resolved_ledger_path = _resolve_ledger_file_path(
        goals_file_path=file_path,
        ledger_file_path=ledger_file_path,
    )

    record_adjustment(
        user_id,
        goal,
        to_money(amount),
        goals=goals[user_id],
        effective_date=effective_date,
        source=source,
        note=note,
        correlation_id=correlation_id,
        ledger_file_path=resolved_ledger_path,
        goals_file_path=file_path,
    )

    logger.info(
        "Recorded adjustment of %s to goal %d for user %d",
        amount,
        goal_id,
        user_id,
    )

    return get_goal_by_id(user_id, goal_id, file_path)


def reverse_goal_ledger_entry(
    user_id: int,
    goal_id: int,
    entry_id: str,
    file_path: Path = DB_PATH,
    ledger_file_path: Path | None = None,
    effective_date: date | None = None,
    source: str = "MANUAL",
    note: str = "",
    correlation_id: str | None = None,
) -> Goal | None:
    """Reverse a ledger entry belonging to a goal."""
    _ensure_loaded(user_id, file_path)

    goal = get_goal_by_id(user_id, goal_id, file_path)

    if goal is None:
        return None

    resolved_ledger_path = _resolve_ledger_file_path(
        goals_file_path=file_path,
        ledger_file_path=ledger_file_path,
    )

    reverse_entry(
        user_id,
        entry_id,
        goal=goal,
        goals=goals[user_id],
        effective_date=effective_date,
        source=source,
        note=note,
        correlation_id=correlation_id,
        ledger_file_path=resolved_ledger_path,
        goals_file_path=file_path,
    )

    logger.info(
        "Reversed ledger entry %s for goal %d for user %d",
        entry_id,
        goal_id,
        user_id,
    )

    return get_goal_by_id(user_id, goal_id, file_path)


def get_goal_ledger_entries(
    user_id: int,
    goal_id: int,
    ledger_file_path: Path = DB_PATH,
) -> list[GoalLedgerEntry]:
    """Return all ledger entries recorded for one of this user's goals."""
    _ensure_loaded(user_id, ledger_file_path)

    entries = load_goal_ledger_from_file(user_id, ledger_file_path)

    return [entry for entry in entries if entry.goal_id == goal_id]


def reconcile_goal(
    user_id: int,
    goal_id: int,
    ledger_file_path: Path = DB_PATH,
) -> tuple[bool, Decimal] | None:
    """Compare a goal's cached balance against its ledger-derived balance."""
    goal = get_goal_by_id(user_id, goal_id, ledger_file_path)

    if goal is None:
        return None

    return reconcile_goal_balance(user_id, goal, ledger_file_path=ledger_file_path)


def delete_goal(
    user_id: int,
    goal_id: int,
    file_path: Path = DB_PATH,
) -> Goal | None:
    """
    Delete one of this user's goals from the active goal list.

    Ledger entries remain preserved as an audit trail.
    """
    _ensure_loaded(user_id, file_path)

    for index, goal in enumerate(goals[user_id]):
        if goal.id != goal_id:
            continue

        deleted_goal = goals[user_id].pop(index)
        save_goals(user_id, file_path)

        remove_goal_planning_request_from_file(
            goal_id,
            file_path=file_path,
        )

        logger.info(
            "Deleted goal %d for user %d",
            goal_id,
            user_id,
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
