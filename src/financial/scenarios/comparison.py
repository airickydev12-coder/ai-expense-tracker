from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from src.core.exceptions import ValidationError
from src.core.money import to_money


class ComparisonDirection(Enum):
    """Direction of change for a compared financial metric."""

    IMPROVEMENT = "Improvement"
    DECLINE = "Decline"
    UNCHANGED = "Unchanged"


@dataclass(frozen=True)
class MetricComparison:
    """Represents the comparison of one financial metric."""

    metric: str
    original_value: Decimal
    projected_value: Decimal
    change: Decimal
    percentage_change: float | None
    direction: ComparisonDirection
    higher_is_better: bool

    def __post_init__(self) -> None:
        """Validate and normalize the metric name."""
        normalized_metric = self.metric.strip()

        if not normalized_metric:
            raise ValidationError("Comparison metric cannot be empty.")

        object.__setattr__(
            self,
            "metric",
            normalized_metric,
        )

    def to_dict(self) -> dict:
        """Convert the comparison to a dictionary."""
        return {
            "metric": self.metric,
            "original_value": self.original_value,
            "projected_value": self.projected_value,
            "change": self.change,
            "percentage_change": self.percentage_change,
            "direction": self.direction.value,
            "higher_is_better": self.higher_is_better,
        }


DEFAULT_METRIC_CONFIGURATION = {
    "total_income": {
        "label": "Total Income",
        "higher_is_better": True,
    },
    "total_expenses": {
        "label": "Total Expenses",
        "higher_is_better": False,
    },
    "net_cash_flow": {
        "label": "Net Cash Flow",
        "higher_is_better": True,
    },
    "total_account_balance": {
        "label": "Account Balance",
        "higher_is_better": True,
    },
    "total_goal_progress": {
        "label": "Goal Progress",
        "higher_is_better": True,
    },
    "total_debt": {
        "label": "Total Debt",
        "higher_is_better": False,
    },
    "net_worth": {
        "label": "Net Worth",
        "higher_is_better": True,
    },
    "health_score": {
        "label": "Health Score",
        "higher_is_better": True,
    },
}


def calculate_percentage_change(
    original_value: Decimal,
    projected_value: Decimal,
) -> float | None:
    """Calculate percentage change from original to projected value."""
    if original_value == 0:
        return None

    return float(
        (projected_value - original_value) / abs(original_value) * 100
    )


def classify_comparison_direction(
    *,
    change: Decimal,
    higher_is_better: bool,
    tolerance: Decimal = Decimal("0.005"),
) -> ComparisonDirection:
    """Classify whether a metric change improves the user's position."""
    if abs(change) <= tolerance:
        return ComparisonDirection.UNCHANGED

    if higher_is_better:
        if change > 0:
            return ComparisonDirection.IMPROVEMENT

        return ComparisonDirection.DECLINE

    if change < 0:
        return ComparisonDirection.IMPROVEMENT

    return ComparisonDirection.DECLINE


def compare_metric(
    *,
    metric: str,
    original_value: Decimal | float | int | str,
    projected_value: Decimal | float | int | str,
    higher_is_better: bool,
) -> MetricComparison:
    """Compare one original and projected financial metric."""
    normalized_original = to_money(original_value)
    normalized_projected = to_money(projected_value)

    change = normalized_projected - normalized_original

    return MetricComparison(
        metric=metric,
        original_value=normalized_original,
        projected_value=normalized_projected,
        change=change,
        percentage_change=calculate_percentage_change(
            normalized_original,
            normalized_projected,
        ),
        direction=classify_comparison_direction(
            change=change,
            higher_is_better=higher_is_better,
        ),
        higher_is_better=higher_is_better,
    )


def compare_snapshots(
    original_snapshot: dict,
    projected_snapshot: dict,
    metric_configuration: dict | None = None,
) -> list[MetricComparison]:
    """Compare configured metrics across two financial snapshots."""
    configuration = (
        metric_configuration
        if metric_configuration is not None
        else DEFAULT_METRIC_CONFIGURATION
    )

    comparisons: list[MetricComparison] = []

    for field_name, settings in configuration.items():
        if field_name not in original_snapshot:
            continue

        if field_name not in projected_snapshot:
            continue

        comparisons.append(
            compare_metric(
                metric=str(settings["label"]),
                original_value=original_snapshot[field_name],
                projected_value=projected_snapshot[field_name],
                higher_is_better=bool(settings["higher_is_better"]),
            )
        )

    return comparisons
