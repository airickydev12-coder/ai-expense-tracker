from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from src.financial.goal_ledger.models import (
    GoalLedgerEntry,
    GoalLedgerEntryType,
)
from src.financial.goal_ledger.repository import (
    append_goal_ledger_entry,
    load_goal_ledger_from_file,
    save_goal_ledger_to_file,
)

USER_ID = 1


def build_entry(
    *,
    goal_id: int = 1,
    entry_type: GoalLedgerEntryType = GoalLedgerEntryType.CONTRIBUTION,
    amount: Decimal = Decimal("100.00"),
    reverses_entry_id: str | None = None,
) -> GoalLedgerEntry:
    return GoalLedgerEntry(
        entry_id=str(uuid4()),
        goal_id=goal_id,
        entry_type=entry_type,
        amount=amount,
        effective_date=date(2026, 7, 1),
        created_at=datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc),
        reverses_entry_id=reverses_entry_id,
    )


def test_save_and_load_goal_ledger(db_path):
    original_entries = [
        build_entry(goal_id=1),
        build_entry(goal_id=2, amount=Decimal("250.00")),
    ]

    save_goal_ledger_to_file(
        original_entries,
        USER_ID,
        db_path,
    )

    loaded_entries = load_goal_ledger_from_file(USER_ID, db_path)

    assert loaded_entries == original_entries


def test_load_goal_ledger_returns_empty_list_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_goal_ledger.db"

    assert load_goal_ledger_from_file(USER_ID, db_path) == []


def test_save_goal_ledger_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "goal_ledger.db"

    save_goal_ledger_to_file(
        [build_entry()],
        USER_ID,
        db_path,
    )

    assert db_path.exists()


def test_load_goal_ledger_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "goal_ledger.db"
    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load goal ledger",
    ):
        load_goal_ledger_from_file(USER_ID, db_path)


def test_append_goal_ledger_entry(db_path):
    first_entry = build_entry(goal_id=1)

    append_goal_ledger_entry(first_entry, USER_ID, db_path)

    second_entry = build_entry(goal_id=1, amount=Decimal("50.00"))

    append_goal_ledger_entry(second_entry, USER_ID, db_path)

    loaded_entries = load_goal_ledger_from_file(USER_ID, db_path)

    assert loaded_entries == [first_entry, second_entry]


def test_save_goal_ledger_rejects_duplicate_entry_ids(db_path):
    entry_one = build_entry(goal_id=1)
    entry_two = build_entry(goal_id=2)

    object.__setattr__(entry_two, "entry_id", entry_one.entry_id)

    with pytest.raises(
        ValueError,
        match="duplicate entry IDs",
    ):
        save_goal_ledger_to_file(
            [entry_one, entry_two],
            USER_ID,
            db_path,
        )
