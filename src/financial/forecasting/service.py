from datetime import datetime, timezone

from src.core.exceptions import ValidationError
from src.financial.forecasting.models import FinancialForecast
from src.financial.forecasting.projections import (
    project_account_balance,
    project_cash_flow,
    project_goal_progress,
    project_health_score,
    project_net_worth,
    project_total_debt,
    validate_forecast_horizon,
)
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.service import get_history


def build_financial_forecast(
    history: list[FinancialSnapshotRecord],
    horizon_days: int,
) -> FinancialForecast:
    """Build a complete forecast from historical snapshots."""
    validate_forecast_horizon(horizon_days)

    if not history:
        raise ValidationError(
            "At least one historical snapshot is required "
            "to build a forecast."
        )

    return FinancialForecast(
        generated_at=datetime.now(timezone.utc),
        horizon_days=horizon_days,
        history_points=len(history),
        net_worth=project_net_worth(
            history,
            horizon_days,
        ),
        cash_flow=project_cash_flow(
            history,
            horizon_days,
        ),
        account_balance=project_account_balance(
            history,
            horizon_days,
        ),
        goal_progress=project_goal_progress(
            history,
            horizon_days,
        ),
        total_debt=project_total_debt(
            history,
            horizon_days,
        ),
        health_score=project_health_score(
            history,
            horizon_days,
        ),
    )


def build_current_financial_forecast(
    horizon_days: int,
) -> FinancialForecast:
    """Build a forecast from the currently loaded history."""
    history = get_history()

    return build_financial_forecast(
        history=history,
        horizon_days=horizon_days,
    )


def build_standard_forecasts(
    history: list[FinancialSnapshotRecord] | None = None,
) -> dict[int, FinancialForecast]:
    """Build standard 30-, 90-, and 365-day forecasts."""
    forecast_history = (
        history
        if history is not None
        else get_history()
    )

    return {
        horizon: build_financial_forecast(
            history=forecast_history,
            horizon_days=horizon,
        )
        for horizon in (30, 90, 365)
    }