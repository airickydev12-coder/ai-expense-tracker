from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.repository import (
    load_history_from_file,
    save_history_to_file,
)

USER_ID = 1


def build_record() -> FinancialSnapshotRecord:
    """Create a historical record for repository tests."""
    return FinancialSnapshotRecord(
        timestamp=datetime(
            2026,
            7,
            12,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        total_income=Decimal("5000"),
        total_expenses=Decimal("1500"),
        net_cash_flow=Decimal("3500"),
        total_account_balance=Decimal("2000"),
        total_goal_progress=Decimal("2500"),
        total_debt=Decimal("1000"),
        net_worth=Decimal("3500"),
        health_score=85,
        health_status="Excellent",
    )


def test_save_and_load_financial_history(db_path):
    original_history = [build_record()]

    save_history_to_file(
        original_history,
        USER_ID,
        db_path,
    )

    loaded_history = load_history_from_file(USER_ID, db_path)

    assert loaded_history == original_history


def test_load_history_returns_empty_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_history.db"

    assert load_history_from_file(USER_ID, db_path) == []


def test_save_history_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "financial_history.db"

    save_history_to_file(
        [build_record()],
        USER_ID,
        db_path,
    )

    assert db_path.exists()


def test_load_history_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "financial_history.db"

    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load history",
    ):
        load_history_from_file(USER_ID, db_path)


def test_save_and_load_history_round_trips_category_totals(db_path):
    record = build_record()
    record.category_totals = {
        "Food": Decimal("245.50"),
        "Utilities": Decimal("125.00"),
    }

    save_history_to_file([record], USER_ID, db_path)

    loaded_history = load_history_from_file(USER_ID, db_path)

    assert loaded_history == [record]
    assert loaded_history[0].category_totals == {
        "Food": Decimal("245.50"),
        "Utilities": Decimal("125.00"),
    }


def test_load_history_defaults_missing_category_totals_to_empty_dict(db_path):
    """A legacy row with no matching category-totals row loads as {}."""
    save_history_to_file([build_record()], USER_ID, db_path)

    loaded_history = load_history_from_file(USER_ID, db_path)

    assert loaded_history[0].category_totals == {}
