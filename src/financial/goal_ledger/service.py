"""Application services for the append-only goal ledger."""

from collections.abc import Sequence
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import TypeAlias
from uuid import uuid4

from src.core.config import DB_PATH
from src.core.exceptions import NotFoundError, ValidationError
from src.core.logging import get_logger
from src.core.money import (
    ZERO,
    add_money,
    subtract_money,
    to_money,
)
from src.financial.goal_ledger.calculator import (
    calculate_goal_balance,
)
from src.financial.goal_ledger.models import (
    GoalLedgerEntry,
    GoalLedgerEntryType,
)
from src.financial.goal_ledger.repository import (
    append_goal_ledger_entry,
    load_goal_ledger_from_file,
    save_goal_ledger_to_file,
)
from src.financial.goals.models import Goal
from src.financial.goals.repository import (
    save_goals_to_file,
)

logger = get_logger(__name__)

MoneyInput: TypeAlias = Decimal | int | float | str


def create_ledger_entry(
    *,
    goal_id: int,
    entry_type: GoalLedgerEntryType,
    amount: MoneyInput,
    effective_date: date | None = None,
    source: str = "MANUAL",
    note: str = "",
    correlation_id: str | None = None,
    reverses_entry_id: str | None = None,
) -> GoalLedgerEntry:
    """Create a validated immutable ledger entry."""
    return GoalLedgerEntry(
        entry_id=str(uuid4()),
        goal_id=goal_id,
        entry_type=entry_type,
        amount=to_money(amount),
        effective_date=(effective_date or date.today()),
        created_at=datetime.now(timezone.utc),
        source=source,
        note=note,
        correlation_id=correlation_id,
        reverses_entry_id=reverses_entry_id,
    )


def migrate_existing_goal_balances(
    user_id: int,
    goals: Sequence[Goal],
    *,
    ledger_file_path: Path = DB_PATH,
) -> list[GoalLedgerEntry]:
    """
    Convert existing cached balances to opening entries.

    A goal is migrated only when it has no ledger records.
    Repeated calls are idempotent.
    """
    entries = load_goal_ledger_from_file(user_id, ledger_file_path)

    goal_ids_with_entries = {entry.goal_id for entry in entries}

    migrated_entries: list[GoalLedgerEntry] = []

    for goal in goals:
        if goal.id in goal_ids_with_entries:
            continue

        if goal.current_amount == ZERO:
            continue

        entry = create_ledger_entry(
            goal_id=goal.id,
            entry_type=(GoalLedgerEntryType.OPENING_BALANCE),
            amount=goal.current_amount,
            source="MIGRATION",
            note="Migrated existing goal balance.",
            correlation_id=(f"goal-opening-balance:{goal.id}"),
        )

        entries.append(entry)
        migrated_entries.append(entry)
        goal_ids_with_entries.add(goal.id)

    if migrated_entries:
        save_goal_ledger_to_file(
            entries,
            user_id,
            ledger_file_path,
        )

    return migrated_entries


def record_contribution(
    user_id: int,
    goal: Goal,
    amount: MoneyInput,
    *,
    goals: list[Goal],
    effective_date: date | None = None,
    source: str = "MANUAL",
    note: str = "",
    correlation_id: str | None = None,
    ledger_file_path: Path = DB_PATH,
    goals_file_path: Path = DB_PATH,
) -> GoalLedgerEntry | None:
    """
    Record a contribution and rebuild the cached balance.

    Contributions exceeding the remaining target are capped at
    the amount required to complete the goal.
    """
    normalized_amount = to_money(amount)

    if normalized_amount < ZERO:
        raise ValidationError("Goal contribution cannot be negative.")

    if normalized_amount == ZERO:
        raise ValidationError("Goal contribution must be greater than zero.")

    migrate_existing_goal_balances(
        user_id,
        [goal],
        ledger_file_path=ledger_file_path,
    )

    remaining_amount = subtract_money(
        goal.target_amount,
        goal.current_amount,
    )

    if remaining_amount < ZERO:
        remaining_amount = ZERO

    if remaining_amount == ZERO:
        return None

    recorded_amount = min(
        normalized_amount,
        remaining_amount,
    )

    entry = create_ledger_entry(
        goal_id=goal.id,
        entry_type=GoalLedgerEntryType.CONTRIBUTION,
        amount=recorded_amount,
        effective_date=effective_date,
        source=source,
        note=note,
        correlation_id=correlation_id,
    )

    _append_entry_and_refresh_cache(
        user_id,
        entry,
        goal=goal,
        goals=goals,
        ledger_file_path=ledger_file_path,
        goals_file_path=goals_file_path,
    )

    logger.info(
        "Recorded contribution of %s to goal %d for user %d",
        recorded_amount,
        goal.id,
        user_id,
    )

    return entry


def record_withdrawal(
    user_id: int,
    goal: Goal,
    amount: MoneyInput,
    *,
    goals: list[Goal],
    effective_date: date | None = None,
    source: str = "MANUAL",
    note: str = "",
    correlation_id: str | None = None,
    ledger_file_path: Path = DB_PATH,
    goals_file_path: Path = DB_PATH,
) -> GoalLedgerEntry:
    """Record a withdrawal and rebuild the cached balance."""
    normalized_amount = to_money(amount)

    if normalized_amount < ZERO:
        raise ValidationError("Goal withdrawal cannot be negative.")

    if normalized_amount == ZERO:
        raise ValidationError("Goal withdrawal must be greater than zero.")

    migrate_existing_goal_balances(
        user_id,
        [goal],
        ledger_file_path=ledger_file_path,
    )

    if normalized_amount > goal.current_amount:
        raise ValidationError(
            "Goal withdrawal cannot exceed the " "current goal balance."
        )

    entry = create_ledger_entry(
        goal_id=goal.id,
        entry_type=GoalLedgerEntryType.WITHDRAWAL,
        amount=normalized_amount,
        effective_date=effective_date,
        source=source,
        note=note,
        correlation_id=correlation_id,
    )

    _append_entry_and_refresh_cache(
        user_id,
        entry,
        goal=goal,
        goals=goals,
        ledger_file_path=ledger_file_path,
        goals_file_path=goals_file_path,
    )

    logger.info(
        "Recorded withdrawal of %s from goal %d for user %d",
        normalized_amount,
        goal.id,
        user_id,
    )

    return entry


def record_adjustment(
    user_id: int,
    goal: Goal,
    amount: MoneyInput,
    *,
    goals: list[Goal],
    effective_date: date | None = None,
    source: str = "MANUAL",
    note: str = "",
    correlation_id: str | None = None,
    ledger_file_path: Path = DB_PATH,
    goals_file_path: Path = DB_PATH,
) -> GoalLedgerEntry:
    """Record a signed balance correction."""
    normalized_amount = to_money(amount)

    if normalized_amount == ZERO:
        raise ValidationError("Goal adjustment cannot be zero.")

    migrate_existing_goal_balances(
        user_id,
        [goal],
        ledger_file_path=ledger_file_path,
    )

    projected_balance = add_money(
        goal.current_amount,
        normalized_amount,
    )

    if projected_balance < ZERO:
        raise ValidationError("Goal adjustment cannot produce " "a negative balance.")

    if projected_balance > goal.target_amount:
        raise ValidationError(
            "Goal adjustment cannot produce a " "balance above the target amount."
        )

    entry = create_ledger_entry(
        goal_id=goal.id,
        entry_type=GoalLedgerEntryType.ADJUSTMENT,
        amount=normalized_amount,
        effective_date=effective_date,
        source=source,
        note=note,
        correlation_id=correlation_id,
    )

    _append_entry_and_refresh_cache(
        user_id,
        entry,
        goal=goal,
        goals=goals,
        ledger_file_path=ledger_file_path,
        goals_file_path=goals_file_path,
    )

    logger.info(
        "Recorded adjustment of %s to goal %d for user %d",
        normalized_amount,
        goal.id,
        user_id,
    )

    return entry


def reverse_entry(
    user_id: int,
    entry_id: str,
    *,
    goal: Goal,
    goals: list[Goal],
    effective_date: date | None = None,
    source: str = "MANUAL",
    note: str = "",
    correlation_id: str | None = None,
    ledger_file_path: Path = DB_PATH,
    goals_file_path: Path = DB_PATH,
) -> GoalLedgerEntry:
    """Reverse a ledger entry without modifying history."""
    entries = load_goal_ledger_from_file(user_id, ledger_file_path)

    original = next(
        (entry for entry in entries if entry.entry_id == entry_id),
        None,
    )

    if original is None:
        raise NotFoundError("Goal ledger entry was not found.")

    if original.goal_id != goal.id:
        raise ValidationError(
            "The ledger entry does not belong " "to the selected goal."
        )

    if original.entry_type is GoalLedgerEntryType.REVERSAL:
        raise ValidationError("A reversal entry cannot be reversed.")

    if any(entry.reverses_entry_id == entry_id for entry in entries):
        raise ValidationError("The ledger entry has already been reversed.")

    reversal = create_ledger_entry(
        goal_id=goal.id,
        entry_type=GoalLedgerEntryType.REVERSAL,
        amount=abs(original.amount),
        effective_date=effective_date,
        source=source,
        note=(note or f"Reversal of ledger entry {entry_id}."),
        correlation_id=correlation_id,
        reverses_entry_id=entry_id,
    )

    _append_entry_and_refresh_cache(
        user_id,
        reversal,
        goal=goal,
        goals=goals,
        ledger_file_path=ledger_file_path,
        goals_file_path=goals_file_path,
    )

    logger.info(
        "Reversed goal ledger entry %s for goal %d for user %d",
        entry_id,
        goal.id,
        user_id,
    )

    return reversal


def reconcile_goal_balance(
    user_id: int,
    goal: Goal,
    *,
    ledger_file_path: Path = DB_PATH,
) -> tuple[bool, Decimal]:
    """Compare cached and ledger-derived balances."""
    entries = load_goal_ledger_from_file(user_id, ledger_file_path)

    ledger_balance = calculate_goal_balance(
        entries,
        goal_id=goal.id,
    )

    is_reconciled = goal.current_amount == ledger_balance

    return is_reconciled, ledger_balance


def rebuild_goal_balance_cache(
    user_id: int,
    goal: Goal,
    *,
    goals: list[Goal],
    ledger_file_path: Path = DB_PATH,
    goals_file_path: Path = DB_PATH,
) -> Goal:
    """Rebuild one cached balance from the ledger."""
    entries = load_goal_ledger_from_file(user_id, ledger_file_path)

    ledger_balance = calculate_goal_balance(
        entries,
        goal_id=goal.id,
    )

    return _replace_cached_goal(
        user_id,
        goal,
        current_amount=ledger_balance,
        goals=goals,
        goals_file_path=goals_file_path,
    )


def _append_entry_and_refresh_cache(
    user_id: int,
    entry: GoalLedgerEntry,
    *,
    goal: Goal,
    goals: list[Goal],
    ledger_file_path: Path,
    goals_file_path: Path,
) -> Goal:
    """
    Append an authoritative entry and refresh the cache.

    The ledger remains authoritative if saving the cached Goal
    fails. The cached balance can subsequently be rebuilt.
    """
    append_goal_ledger_entry(
        entry,
        user_id,
        ledger_file_path,
    )

    return rebuild_goal_balance_cache(
        user_id,
        goal,
        goals=goals,
        ledger_file_path=ledger_file_path,
        goals_file_path=goals_file_path,
    )


def _replace_cached_goal(
    user_id: int,
    goal: Goal,
    *,
    current_amount: MoneyInput,
    goals: list[Goal],
    goals_file_path: Path,
) -> Goal:
    """Replace a Goal with its rebuilt cached balance."""
    updated_goal = Goal(
        id=goal.id,
        name=goal.name,
        target_amount=goal.target_amount,
        current_amount=to_money(current_amount),
    )

    for index, existing_goal in enumerate(goals):
        if existing_goal.id != goal.id:
            continue

        goals[index] = updated_goal

        save_goals_to_file(
            goals,
            user_id,
            goals_file_path,
        )

        return updated_goal

    raise NotFoundError("Goal was not found in application memory.")
