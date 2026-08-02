"""Tests for the financial forecasting API endpoints."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.history.service import clear_history, record_snapshot

client = TestClient(app)


def setup_function() -> None:
    """Reset in-memory history and seed it with two snapshots."""
    clear_history()

    now = datetime.now(timezone.utc)

    record_snapshot(
        {
            "total_income": Decimal("4000"),
            "total_expenses": Decimal("2500"),
            "net_cash_flow": Decimal("1500"),
            "total_account_balance": Decimal("3000"),
            "total_goal_progress": Decimal("1000"),
            "total_debt": Decimal("10000"),
            "net_worth": Decimal("-6000"),
            "health_score": 50,
            "health_status": "Fair",
        },
        timestamp=now - timedelta(days=30),
    )
    record_snapshot(
        {
            "total_income": Decimal("5000"),
            "total_expenses": Decimal("2500"),
            "net_cash_flow": Decimal("2500"),
            "total_account_balance": Decimal("4500"),
            "total_goal_progress": Decimal("1600"),
            "total_debt": Decimal("8500"),
            "net_worth": Decimal("-2400"),
            "health_score": 65,
            "health_status": "Good",
        },
        timestamp=now,
    )


def test_get_forecast_requires_positive_horizon() -> None:
    response = client.get("/forecasting", params={"horizon_days": 0})

    assert response.status_code == 422


def test_get_forecast() -> None:
    response = client.get("/forecasting", params={"horizon_days": 30})

    assert response.status_code == 200
    body = response.json()
    assert body["horizon_days"] == 30
    assert body["history_points"] == 2
    assert body["net_worth"]["metric"] == "Net Worth"


def test_get_standard_forecasts() -> None:
    response = client.get("/forecasting/standard")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"30", "90", "365"}
    assert body["30"]["horizon_days"] == 30
    assert body["365"]["horizon_days"] == 365
