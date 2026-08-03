"""SQLite persistence for the append-only goal ledger."""

import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError, ValidationError
from src.core.logging import get_logger
from src.financial.goal_ledger.models import (
    GoalLedgerEntry,
    GoalLedgerEntryType,
)

logger = get_logger(__name__)


def load_goal_ledger_from_file(
    user_id: int,
    db_path: Path = DB_PATH,
) -> list[GoalLedgerEntry]:
    """Load all of this user's goal-ledger entries."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                """
                SELECT entry_id, goal_id, entry_type, amount, effective_date,
                       created_at, source, note, correlation_id, reverses_entry_id
                FROM goal_ledger_entries WHERE user_id = ? ORDER BY created_at
                """,
                (user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load goal ledger from {db_path}") from error

    entries = [GoalLedgerEntry.from_dict(dict(row)) for row in rows]

    _validate_ledger(entries)

    logger.debug(
        "Loaded %d goal ledger entry(ies) for user %d from %s",
        len(entries),
        user_id,
        db_path,
    )

    return entries


def save_goal_ledger_to_file(
    entries: list[GoalLedgerEntry],
    user_id: int,
    db_path: Path = DB_PATH,
) -> None:
    """Save this user's complete ledger, replacing their existing rows."""
    _validate_ledger(entries)

    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM goal_ledger_entries WHERE user_id = ?", (user_id,))
            connection.executemany(
                """
                INSERT INTO goal_ledger_entries (
                    entry_id, goal_id, entry_type, amount, effective_date,
                    created_at, source, note, correlation_id, reverses_entry_id, user_id
                )
                VALUES (
                    :entry_id, :goal_id, :entry_type, :amount, :effective_date,
                    :created_at, :source, :note, :correlation_id, :reverses_entry_id, :user_id
                )
                """,
                [{**entry.to_dict(), "user_id": user_id} for entry in entries],
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to save goal ledger to {db_path}") from error

    logger.debug(
        "Saved %d goal ledger entry(ies) for user %d to %s",
        len(entries),
        user_id,
        db_path,
    )


def append_goal_ledger_entry(
    entry: GoalLedgerEntry,
    user_id: int,
    db_path: Path = DB_PATH,
) -> None:
    """Append one immutable entry to this user's ledger."""
    entries = load_goal_ledger_from_file(user_id, db_path)

    entries.append(entry)

    save_goal_ledger_to_file(
        entries,
        user_id,
        db_path,
    )


def _validate_ledger(
    entries: list[GoalLedgerEntry],
) -> None:
    """Validate ledger-wide integrity constraints."""
    entry_ids = [entry.entry_id for entry in entries]

    if len(entry_ids) != len(set(entry_ids)):
        raise ValidationError("Goal ledger contains duplicate entry IDs.")

    correlation_ids = [
        entry.correlation_id for entry in entries if entry.correlation_id is not None
    ]

    if len(correlation_ids) != len(set(correlation_ids)):
        raise ValidationError("Goal ledger contains duplicate " "correlation IDs.")

    entries_by_id = {entry.entry_id: entry for entry in entries}

    reversed_entry_ids: set[str] = set()

    for entry in entries:
        original_entry_id = entry.reverses_entry_id

        if original_entry_id is None:
            continue

        original_entry = entries_by_id.get(original_entry_id)

        if original_entry is None:
            raise ValidationError(
                "Goal ledger reversal references " "an unknown entry."
            )

        if original_entry.goal_id != entry.goal_id:
            raise ValidationError(
                "A reversal must reference an entry " "for the same goal."
            )

        if original_entry.entry_type is GoalLedgerEntryType.REVERSAL:
            raise ValidationError("A reversal cannot reverse another reversal.")

        if original_entry_id in reversed_entry_ids:
            raise ValidationError("A ledger entry cannot be reversed twice.")

        if entry.amount != abs(original_entry.amount):
            raise ValidationError(
                "A reversal amount must equal the " "original entry amount."
            )

        reversed_entry_ids.add(original_entry_id)
