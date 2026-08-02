"""Financial forecasting API endpoints."""

from fastapi import APIRouter, Query

from src.api.schemas.forecasting import FinancialForecastResponse
from src.financial.forecasting.service import (
    build_current_financial_forecast,
    build_standard_forecasts,
)

router = APIRouter(prefix="/forecasting", tags=["Forecasting"])


@router.get("", response_model=FinancialForecastResponse)
def get_forecast(
    horizon_days: int = Query(gt=0),
) -> FinancialForecastResponse:
    """Return a financial forecast for the given horizon."""
    forecast = build_current_financial_forecast(horizon_days)
    return FinancialForecastResponse.model_validate(forecast)


@router.get("/standard", response_model=dict[str, FinancialForecastResponse])
def get_standard_forecasts() -> dict[str, FinancialForecastResponse]:
    """Return forecasts for the standard 30/90/365-day horizons."""
    forecasts = build_standard_forecasts()
    return {
        str(horizon_days): FinancialForecastResponse.model_validate(forecast)
        for horizon_days, forecast in forecasts.items()
    }
