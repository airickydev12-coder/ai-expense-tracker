"""API schemas for financial forecasting endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MetricProjectionResponse(BaseModel):
    """Serialized representation of one projected financial metric."""

    model_config = ConfigDict(from_attributes=True)

    metric: str
    current_value: float
    projected_value: float
    projected_change: float
    daily_change: float
    horizon_days: int


class FinancialForecastResponse(BaseModel):
    """Serialized representation of a complete financial forecast."""

    model_config = ConfigDict(from_attributes=True)

    generated_at: datetime
    horizon_days: int
    history_points: int
    net_worth: MetricProjectionResponse
    cash_flow: MetricProjectionResponse
    account_balance: MetricProjectionResponse
    goal_progress: MetricProjectionResponse
    total_debt: MetricProjectionResponse
    health_score: MetricProjectionResponse
