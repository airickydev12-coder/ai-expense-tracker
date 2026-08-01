import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.repository import (
    load_history_from_file,
    save_history_to_file,
)


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


def test_save_and_load_financial_history(tmp_path):
    file_path = tmp_path / "financial_history.json"

    original_history = [build_record()]

    save_history_to_file(
        original_history,
        file_path,
    )

    loaded_history = load_history_from_file(file_path)

    assert loaded_history == original_history


def test_load_history_returns_empty_when_file_missing(
    tmp_path,
):
    file_path = tmp_path / "missing_history.json"

    assert load_history_from_file(file_path) == []


def test_save_history_creates_parent_directory(
    tmp_path,
):
    file_path = tmp_path / "nested" / "data" / "financial_history.json"

    save_history_to_file(
        [build_record()],
        file_path,
    )

    assert file_path.exists()


def test_load_history_rejects_invalid_json(
    tmp_path,
):
    file_path = tmp_path / "financial_history.json"

    file_path.write_text(
        "not valid json",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="invalid JSON",
    ):
        load_history_from_file(file_path)


def test_load_history_rejects_non_list_json(
    tmp_path,
):
    file_path = tmp_path / "financial_history.json"

    file_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-07-12T12:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="JSON list",
    ):
        load_history_from_file(file_path)
