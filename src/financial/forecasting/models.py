from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class MetricProjection:
    """Represents a projected financial metric."""

    metric: str
    current_value: Decimal
    projected_value: Decimal
    projected_change: Decimal
    daily_change: Decimal
    horizon_days: int

    def to_dict(self) -> dict:
        """Convert the metric projection to a dictionary."""
        return {
            "metric": self.metric,
            "current_value": self.current_value,
            "projected_value": self.projected_value,
            "projected_change": self.projected_change,
            "daily_change": self.daily_change,
            "horizon_days": self.horizon_days,
        }


@dataclass(frozen=True)
class FinancialForecast:
    """Represents a complete financial forecast."""

    generated_at: datetime
    horizon_days: int
    history_points: int
    net_worth: MetricProjection
    cash_flow: MetricProjection
    account_balance: MetricProjection
    goal_progress: MetricProjection
    total_debt: MetricProjection
    health_score: MetricProjection

    def to_dict(self) -> dict:
        """Convert the complete forecast to a dictionary."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "horizon_days": self.horizon_days,
            "history_points": self.history_points,
            "net_worth": self.net_worth.to_dict(),
            "cash_flow": self.cash_flow.to_dict(),
            "account_balance": self.account_balance.to_dict(),
            "goal_progress": self.goal_progress.to_dict(),
            "total_debt": self.total_debt.to_dict(),
            "health_score": self.health_score.to_dict(),
        }