from datetime import datetime, timedelta, timezone

from src.financial.history.analytics import (
    get_cash_flow_change,
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
        total_income=4000,
        total_expenses=2000,
        net_cash_flow=2000,
        total_account_balance=1500,
        total_goal_progress=1000,
        total_debt=2000,
        net_worth=500,
        health_score=60,
        health_status="Fair",
    )

    newer = FinancialSnapshotRecord(
        timestamp=now,
        total_income=5000,
        total_expenses=1800,
        net_cash_flow=3200,
        total_account_balance=2500,
        total_goal_progress=2000,
        total_debt=1500,
        net_worth=3000,
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