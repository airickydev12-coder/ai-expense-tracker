"""JSON repository for the append-only goal ledger."""

import json
from pathlib import Path
from typing import Any

from src.core.config import GOAL_LEDGER_FILE
from src.core.exceptions import PersistenceError, ValidationError
from src.core.logging import get_logger
from src.financial.goal_ledger.models import (
    GoalLedgerEntry,
    GoalLedgerEntryType,
)

logger = get_logger(__name__)

LEDGER_SCHEMA_VERSION = 1


def load_goal_ledger_from_file(
    file_path: Path = GOAL_LEDGER_FILE,
) -> list[GoalLedgerEntry]:
    """Load all goal-ledger entries."""
    if not file_path.exists():
        return []

    try:
        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            raw_document = json.load(file)
    except json.JSONDecodeError as error:
        logger.error(
            "Failed to parse goal ledger file %s: %s",
            file_path,
            error,
        )
        raise PersistenceError(f"Goal ledger contains invalid JSON: {file_path}") from error
    except OSError as error:
        logger.error(
            "Failed to read goal ledger file %s: %s",
            file_path,
            error,
        )
        raise PersistenceError(f"Unable to read goal ledger: {file_path}") from error

    if not isinstance(raw_document, dict):
        raise PersistenceError("Goal ledger must be stored as a JSON object.")

    schema_version = raw_document.get("schema_version")

    if schema_version != LEDGER_SCHEMA_VERSION:
        raise PersistenceError(
            "Unsupported goal-ledger schema version: " f"{schema_version!r}."
        )

    raw_entries = raw_document.get("entries")

    if not isinstance(raw_entries, list):
        raise PersistenceError("Goal ledger entries must be stored " "as a JSON list.")

    entries = [GoalLedgerEntry.from_dict(raw_entry) for raw_entry in raw_entries]

    _validate_ledger(entries)

    logger.debug(
        "Loaded %d goal ledger entry(ies) from %s",
        len(entries),
        file_path,
    )

    return entries


def save_goal_ledger_to_file(
    entries: list[GoalLedgerEntry],
    file_path: Path = GOAL_LEDGER_FILE,
) -> None:
    """Atomically save the complete ledger."""
    _validate_ledger(entries)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    document: dict[str, Any] = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "entries": [entry.to_dict() for entry in entries],
    }

    temporary_path = file_path.with_suffix(file_path.suffix + ".tmp")

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                document,
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
        "Saved %d goal ledger entry(ies) to %s",
        len(entries),
        file_path,
    )


def append_goal_ledger_entry(
    entry: GoalLedgerEntry,
    file_path: Path = GOAL_LEDGER_FILE,
) -> None:
    """Append one immutable entry to the ledger."""
    entries = load_goal_ledger_from_file(file_path)

    entries.append(entry)

    save_goal_ledger_to_file(
        entries,
        file_path,
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
            raise ValidationError("Goal ledger reversal references " "an unknown entry.")

        if original_entry.goal_id != entry.goal_id:
            raise ValidationError("A reversal must reference an entry " "for the same goal.")

        if original_entry.entry_type is GoalLedgerEntryType.REVERSAL:
            raise ValidationError("A reversal cannot reverse another reversal.")

        if original_entry_id in reversed_entry_ids:
            raise ValidationError("A ledger entry cannot be reversed twice.")

        if entry.amount != abs(original_entry.amount):
            raise ValidationError(
                "A reversal amount must equal the " "original entry amount."
            )

        reversed_entry_ids.add(original_entry_id)
