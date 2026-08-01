from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.financial.forecasting.projections import (
    calculate_daily_change,
    project_account_balance,
    project_cash_flow,
    project_goal_progress,
    project_health_score,
    project_net_worth,
    project_total_debt,
)
from src.financial.history.models import FinancialSnapshotRecord


def build_history() -> list[FinancialSnapshotRecord]:
    """Create 30 days of historical change."""
    now = datetime.now(timezone.utc)

    older = FinancialSnapshotRecord(
        timestamp=now - timedelta(days=30),
        total_income=Decimal("4000"),
        total_expenses=Decimal("2500"),
        net_cash_flow=Decimal("1500"),
        total_account_balance=Decimal("3000"),
        total_goal_progress=Decimal("1000"),
        total_debt=Decimal("10000"),
        net_worth=Decimal("-6000"),
        health_score=50,
        health_status="Fair",
    )

    newer = FinancialSnapshotRecord(
        timestamp=now,
        total_income=Decimal("5000"),
        total_expenses=Decimal("2500"),
        net_cash_flow=Decimal("2500"),
        total_account_balance=Decimal("4500"),
        total_goal_progress=Decimal("1600"),
        total_debt=Decimal("8500"),
        net_worth=Decimal("-2400"),
        health_score=65,
        health_status="Good",
    )

    return [older, newer]


def test_calculate_daily_change():
    history = build_history()

    result = calculate_daily_change(
        history,
        lambda record: record.net_worth,
    )

    assert result == pytest.approx(120)


def test_calculate_daily_change_with_one_record():
    history = [build_history()[0]]

    result = calculate_daily_change(
        history,
        lambda record: record.net_worth,
    )

    assert result == 0


def test_project_net_worth():
    projection = project_net_worth(
        build_history(),
        horizon_days=30,
    )

    assert projection.current_value == -2400
    assert projection.daily_change == pytest.approx(120)
    assert projection.projected_value == pytest.approx(1200)
    assert projection.projected_change == pytest.approx(3600)


def test_project_cash_flow():
    projection = project_cash_flow(
        build_history(),
        horizon_days=30,
    )

    assert projection.current_value == 2500
    assert projection.projected_value == pytest.approx(3500)


def test_project_account_balance():
    projection = project_account_balance(
        build_history(),
        horizon_days=30,
    )

    assert projection.current_value == 4500
    assert projection.projected_value == pytest.approx(6000)


def test_project_goal_progress():
    projection = project_goal_progress(
        build_history(),
        horizon_days=30,
    )

    assert projection.current_value == 1600
    assert projection.projected_value == pytest.approx(2200)


def test_project_total_debt():
    projection = project_total_debt(
        build_history(),
        horizon_days=30,
    )

    assert projection.current_value == 8500
    assert projection.projected_value == pytest.approx(7000)


def test_debt_projection_cannot_be_negative():
    projection = project_total_debt(
        build_history(),
        horizon_days=365,
    )

    assert projection.projected_value == 0
    assert projection.projected_change == -8500


def test_health_score_projection_is_capped_at_100():
    projection = project_health_score(
        build_history(),
        horizon_days=365,
    )

    assert projection.projected_value == 100


def test_projection_rejects_invalid_horizon():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        project_net_worth(
            build_history(),
            horizon_days=0,
        )


def test_projection_rejects_empty_history():
    with pytest.raises(
        ValueError,
        match="historical snapshot",
    ):
        project_net_worth(
            [],
            horizon_days=30,
        )


def test_projection_with_duplicate_timestamps_is_stable():
    history = build_history()

    duplicate_timestamp_history = [
        history[0],
        FinancialSnapshotRecord(
            timestamp=history[0].timestamp,
            total_income=Decimal("5000"),
            total_expenses=Decimal("2500"),
            net_cash_flow=Decimal("2500"),
            total_account_balance=Decimal("4500"),
            total_goal_progress=Decimal("1600"),
            total_debt=Decimal("8500"),
            net_worth=Decimal("-2400"),
            health_score=65,
            health_status="Good",
        ),
    ]

    projection = project_net_worth(
        duplicate_timestamp_history,
        horizon_days=30,
    )

    assert projection.daily_change == 0
    assert projection.projected_value == -2400
