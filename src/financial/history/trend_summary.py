from dataclasses import dataclass
from decimal import Decimal

from src.financial.history.trend_direction import (
    FinancialMomentum,
    TrendDirection,
)


@dataclass(frozen=True)
class MetricTrend:
    """Represents the trend for one financial metric."""

    direction: TrendDirection
    change: Decimal

    def to_dict(self) -> dict:
        """Convert the metric trend to a dictionary."""
        return {
            "direction": self.direction.value,
            "change": self.change,
        }


@dataclass(frozen=True)
class FinancialTrendSummary:
    """Represents an overall financial trend analysis."""

    net_worth: MetricTrend
    cash_flow: MetricTrend
    income: MetricTrend
    expenses: MetricTrend
    health_score: MetricTrend
    overall_momentum: FinancialMomentum

    def to_dict(self) -> dict:
        """Convert the complete trend summary to a dictionary."""
        return {
            "net_worth": self.net_worth.to_dict(),
            "cash_flow": self.cash_flow.to_dict(),
            "income": self.income.to_dict(),
            "expenses": self.expenses.to_dict(),
            "health_score": self.health_score.to_dict(),
            "overall_momentum": self.overall_momentum.value,
        }
