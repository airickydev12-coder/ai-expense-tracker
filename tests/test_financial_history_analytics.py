from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.financial.history.analytics import (
    filter_history_within_days,
    get_cash_flow_change,
    get_category_totals_change,
    get_expense_change,
    get_health_score_change,
    get_income_change,
    get_net_worth_change,
)
from src.financial.history.models import FinancialSnapshotRecord


def build_history() -> list[FinancialSnapshotRecord]:
    """Create historical records for analytics tests."""
    now = datetime.now(timezone.utc)

    older = FinancialSnapshotRecord(
        timestamp=now - timedelta(days=30),
        total_income=Decimal("4000"),
        total_expenses=Decimal("2000"),
        net_cash_flow=Decimal("2000"),
        total_account_balance=Decimal("1500"),
        total_goal_progress=Decimal("1000"),
        total_debt=Decimal("2000"),
        net_worth=Decimal("500"),
        health_score=60,
        health_status="Fair",
    )

    newer = FinancialSnapshotRecord(
        timestamp=now,
        total_income=Decimal("5000"),
        total_expenses=Decimal("1800"),
        net_cash_flow=Decimal("3200"),
        total_account_balance=Decimal("2500"),
        total_goal_progress=Decimal("2000"),
        total_debt=Decimal("1500"),
        net_worth=Decimal("3000"),
        health_score=80,
        health_status="Good",
    )

    return [newer, older]


def test_get_net_worth_change():
    assert get_net_worth_change(build_history()) == 2500


def test_get_cash_flow_change():
    assert get_cash_flow_change(build_history()) == 1200


def test_get_health_score_change():
    assert get_health_score_change(build_history()) == 20


def test_get_income_change():
    assert get_income_change(build_history()) == 1000


def test_get_expense_change():
    assert get_expense_change(build_history()) == -200


def test_analytics_return_zero_with_one_record():
    history = [build_history()[0]]

    assert get_net_worth_change(history) == 0
    assert get_cash_flow_change(history) == 0
    assert get_health_score_change(history) == 0
    assert get_income_change(history) == 0
    assert get_expense_change(history) == 0


def test_analytics_return_zero_with_empty_history():
    assert get_net_worth_change([]) == 0
    assert get_cash_flow_change([]) == 0
    assert get_health_score_change([]) == 0
    assert get_income_change([]) == 0
    assert get_expense_change([]) == 0


def test_filter_history_within_days_excludes_older_records():
    now = datetime.now(timezone.utc)
    newer, older = build_history()

    filtered = filter_history_within_days([newer, older], 31, now=now)

    assert filtered == [older, newer]

    filtered_narrow = filter_history_within_days([newer, older], 10, now=now)

    assert filtered_narrow == [newer]


def test_filter_history_within_days_uses_now_parameter():
    now = datetime.now(timezone.utc)
    newer, older = build_history()

    filtered_future = filter_history_within_days(
        [newer, older],
        31,
        now=now + timedelta(days=40),
    )

    assert filtered_future == []


def test_filter_history_within_days_returns_empty_for_empty_history():
    assert filter_history_within_days([], 31) == []


def test_get_category_totals_change_computes_per_category_delta():
    newer, older = build_history()
    older.category_totals = {"Food": Decimal("200.00"), "Utilities": Decimal("100.00")}
    newer.category_totals = {"Food": Decimal("245.50"), "Utilities": Decimal("100.00")}

    change = get_category_totals_change([newer, older])

    assert change == {"Food": Decimal("45.50"), "Utilities": Decimal("0.00")}


def test_get_category_totals_change_handles_category_added_or_removed():
    newer, older = build_history()
    older.category_totals = {"Food": Decimal("200.00")}
    newer.category_totals = {"Entertainment": Decimal("50.00")}

    change = get_category_totals_change([newer, older])

    assert change == {"Food": Decimal("-200.00"), "Entertainment": Decimal("50.00")}


def test_get_category_totals_change_returns_empty_for_insufficient_history():
    assert get_category_totals_change([build_history()[0]]) == {}


def test_get_category_totals_change_returns_empty_when_no_category_data():
    newer, older = build_history()

    assert get_category_totals_change([newer, older]) == {}
