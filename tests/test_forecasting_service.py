from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.financial.forecasting.service import (
    build_current_financial_forecast,
    build_financial_forecast,
    build_standard_forecasts,
)
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.service import (
    clear_history,
    load_history,
    record_snapshot,
)


def build_history() -> list[FinancialSnapshotRecord]:
    """Create historical snapshots for forecasting tests."""
    now = datetime.now(timezone.utc)

    return [
        FinancialSnapshotRecord(
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
        ),
        FinancialSnapshotRecord(
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
        ),
    ]


def build_snapshot() -> dict:
    """Create a snapshot compatible with history recording."""
    return {
        "total_income": 5000,
        "total_expenses": 2500,
        "net_cash_flow": 2500,
        "total_account_balance": 4500,
        "total_goal_progress": 1600,
        "total_debt": 8500,
        "net_worth": -2400,
        "health_score": 65,
        "health_status": "Good",
    }


def setup_function():
    """Clear loaded history before each test."""
    clear_history()


def teardown_function():
    """Clear loaded history after each test."""
    clear_history()


def test_build_financial_forecast():
    forecast = build_financial_forecast(
        history=build_history(),
        horizon_days=30,
    )

    assert forecast.horizon_days == 30
    assert forecast.history_points == 2
    assert forecast.net_worth.current_value == -2400
    assert forecast.net_worth.projected_value == pytest.approx(1200)
    assert forecast.total_debt.projected_value == pytest.approx(7000)


def test_build_financial_forecast_serialization():
    forecast = build_financial_forecast(
        history=build_history(),
        horizon_days=30,
    )

    data = forecast.to_dict()

    assert data["horizon_days"] == 30
    assert data["history_points"] == 2
    assert data["net_worth"]["metric"] == "Net Worth"
    assert data["total_debt"]["metric"] == "Total Debt"


def test_build_financial_forecast_with_one_snapshot():
    forecast = build_financial_forecast(
        history=[build_history()[-1]],
        horizon_days=30,
    )

    assert forecast.net_worth.daily_change == 0
    assert forecast.net_worth.projected_value == -2400


def test_build_financial_forecast_rejects_empty_history():
    with pytest.raises(
        ValueError,
        match="At least one historical snapshot",
    ):
        build_financial_forecast(
            history=[],
            horizon_days=30,
        )


def test_build_standard_forecasts():
    forecasts = build_standard_forecasts(build_history())

    assert set(forecasts) == {
        30,
        90,
        365,
    }

    assert forecasts[30].horizon_days == 30
    assert forecasts[90].horizon_days == 90
    assert forecasts[365].horizon_days == 365


def test_build_current_financial_forecast(
    tmp_path,
):
    file_path = tmp_path / "financial_history.json"

    load_history(file_path)

    earlier_timestamp = datetime.now(timezone.utc) - timedelta(days=30)

    record_snapshot(
        {
            **build_snapshot(),
            "net_worth": -6000,
            "total_account_balance": 3000,
            "total_goal_progress": 1000,
            "total_debt": 10000,
            "net_cash_flow": 1500,
            "health_score": 50,
            "health_status": "Fair",
        },
        file_path=file_path,
        timestamp=earlier_timestamp,
    )

    record_snapshot(
        build_snapshot(),
        file_path=file_path,
        timestamp=datetime.now(timezone.utc),
    )

    forecast = build_current_financial_forecast(horizon_days=30)

    assert forecast.history_points == 2
    assert forecast.horizon_days == 30
    assert forecast.net_worth.projected_value > (forecast.net_worth.current_value)
