from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.financial.forecasting.models import (
    FinancialForecast,
    MetricProjection,
)
from src.presentation import forecast_cli as cli


def build_forecast() -> FinancialForecast:
    """Create a forecast for CLI tests."""
    projection = MetricProjection(
        metric="Net Worth",
        current_value=Decimal("1000"),
        projected_value=Decimal("1500"),
        projected_change=Decimal("500"),
        daily_change=Decimal("16.67"),
        horizon_days=30,
    )

    return FinancialForecast(
        generated_at=datetime.now(timezone.utc),
        horizon_days=30,
        history_points=2,
        net_worth=projection,
        cash_flow=projection,
        account_balance=projection,
        goal_progress=projection,
        total_debt=projection,
        health_score=projection,
    )


@pytest.mark.parametrize(
    ("selection", "expected"),
    [
        ("1", 30),
        ("2", 90),
        ("3", 365),
        ("4", None),
        ("invalid", None),
    ],
)
def test_select_forecast_horizon(
    monkeypatch,
    selection,
    expected,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: selection,
    )

    result = cli.select_forecast_horizon()

    assert result == expected


def test_display_current_forecast(
    monkeypatch,
):
    captured: dict = {}

    monkeypatch.setattr(
        cli,
        "get_cli_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        cli,
        "select_forecast_horizon",
        lambda: 90,
    )

    def fake_build_forecast(
        user_id: int,
        horizon_days: int,
    ) -> FinancialForecast:
        captured["horizon"] = horizon_days
        return build_forecast()

    monkeypatch.setattr(
        cli,
        "build_current_financial_forecast",
        fake_build_forecast,
    )

    def fake_display(
        forecast: FinancialForecast,
    ) -> None:
        captured["forecast"] = forecast

    monkeypatch.setattr(
        cli,
        "display_financial_forecast",
        fake_display,
    )

    cli.display_current_forecast()

    assert captured["horizon"] == 90
    assert captured["forecast"].history_points == 2


def test_display_current_forecast_handles_missing_history(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        cli,
        "get_cli_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        cli,
        "select_forecast_horizon",
        lambda: 30,
    )

    def fake_build_forecast(
        user_id: int,
        horizon_days: int,
    ) -> FinancialForecast:
        raise ValueError("At least one historical snapshot is required.")

    monkeypatch.setattr(
        cli,
        "build_current_financial_forecast",
        fake_build_forecast,
    )

    cli.display_current_forecast()

    output = capsys.readouterr().out

    assert "Unable to build forecast" in output
    assert "At least one historical snapshot" in output


def test_display_current_forecast_returns_when_back_selected(
    monkeypatch,
):
    monkeypatch.setattr(
        cli,
        "select_forecast_horizon",
        lambda: None,
    )

    cli.display_current_forecast()
