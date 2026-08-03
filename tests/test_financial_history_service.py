from datetime import datetime, timedelta, timezone

from src.financial.history.service import (
    clear_history,
    get_history,
    get_latest_snapshot,
    load_history,
    record_snapshot,
)


def setup_function():
    """Clear history before each service test."""
    clear_history()


def teardown_function():
    """Clear history after each service test."""
    clear_history()


def build_snapshot() -> dict:
    """Create a financial snapshot for history tests."""
    return {
        "total_income": 5000,
        "total_expenses": 1500,
        "net_cash_flow": 3500,
        "total_account_balance": 2000,
        "total_goal_progress": 2500,
        "total_debt": 1000,
        "net_worth": 3500,
        "health_score": 85,
        "health_status": "Excellent",
    }


def test_record_snapshot(tmp_path):
    file_path = tmp_path / "financial_history.json"

    load_history(file_path)

    record = record_snapshot(
        build_snapshot(),
        file_path=file_path,
    )

    assert record.total_income == 5000
    assert record.net_worth == 3500
    assert len(get_history()) == 1
    assert file_path.exists()


def test_record_snapshot_captures_category_totals(tmp_path):
    file_path = tmp_path / "financial_history.json"

    load_history(file_path)

    snapshot = build_snapshot()
    snapshot["category_totals"] = {"Food": 245.50, "Utilities": 125.00}

    record = record_snapshot(
        snapshot,
        file_path=file_path,
    )

    assert record.category_totals == {"Food": 245.50, "Utilities": 125.00}


def test_record_snapshot_defaults_category_totals_when_absent(tmp_path):
    file_path = tmp_path / "financial_history.json"

    load_history(file_path)

    record = record_snapshot(
        build_snapshot(),
        file_path=file_path,
    )

    assert record.category_totals == {}


def test_record_snapshot_is_restored_after_reload(
    tmp_path,
):
    file_path = tmp_path / "financial_history.json"

    load_history(file_path)
    record_snapshot(
        build_snapshot(),
        file_path=file_path,
    )

    clear_history()

    assert get_history() == []

    load_history(file_path)

    history = get_history()

    assert len(history) == 1
    assert history[0].health_status == "Excellent"


def test_get_latest_snapshot_uses_timestamp(
    tmp_path,
):
    file_path = tmp_path / "financial_history.json"

    load_history(file_path)

    now = datetime.now(timezone.utc)

    newer_record = record_snapshot(
        build_snapshot(),
        file_path=file_path,
        timestamp=now,
    )

    record_snapshot(
        build_snapshot(),
        file_path=file_path,
        timestamp=now - timedelta(days=1),
    )

    assert get_latest_snapshot() == newer_record


def test_get_latest_snapshot_returns_none_when_empty():
    assert get_latest_snapshot() is None


def test_get_history_returns_copy(
    tmp_path,
):
    file_path = tmp_path / "financial_history.json"

    load_history(file_path)
    record_snapshot(
        build_snapshot(),
        file_path=file_path,
    )

    returned_history = get_history()
    returned_history.clear()

    assert len(get_history()) == 1
