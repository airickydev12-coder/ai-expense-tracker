from dataclasses import dataclass

from src.financial.scenarios.comparison import (
    ComparisonDirection,
    MetricComparison,
    compare_snapshots,
)
from src.financial.scenarios.models import (
    ScenarioResult,
)


@dataclass(frozen=True)
class ScenarioComparisonReport:
    """Represents a reusable comparison report for one scenario."""

    scenario_name: str
    scenario_type: str
    summary: str
    comparisons: list[MetricComparison]
    improvements: list[MetricComparison]
    declines: list[MetricComparison]
    unchanged: list[MetricComparison]

    def __post_init__(self) -> None:
        """Protect mutable report collections."""
        object.__setattr__(
            self,
            "comparisons",
            self.comparisons.copy(),
        )
        object.__setattr__(
            self,
            "improvements",
            self.improvements.copy(),
        )
        object.__setattr__(
            self,
            "declines",
            self.declines.copy(),
        )
        object.__setattr__(
            self,
            "unchanged",
            self.unchanged.copy(),
        )

    def get_comparison(
        self,
        metric: str,
    ) -> MetricComparison | None:
        """Return one comparison by metric name."""
        normalized_metric = metric.strip().lower()

        for comparison in self.comparisons:
            if comparison.metric.lower() == normalized_metric:
                return comparison

        return None

    def to_dict(self) -> dict:
        """Convert the report to a dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "scenario_type": self.scenario_type,
            "summary": self.summary,
            "comparisons": [comparison.to_dict() for comparison in self.comparisons],
            "improvements": [comparison.to_dict() for comparison in self.improvements],
            "declines": [comparison.to_dict() for comparison in self.declines],
            "unchanged": [comparison.to_dict() for comparison in self.unchanged],
        }


def build_report_summary(
    *,
    improvement_count: int,
    decline_count: int,
    unchanged_count: int,
) -> str:
    """Build a concise natural-language comparison summary."""
    if improvement_count == 0 and decline_count == 0:
        return (
            "The scenario produces no measurable change "
            "in the compared financial metrics."
        )

    if improvement_count > decline_count:
        return (
            "The scenario produces an overall improvement "
            f"across {improvement_count} financial metrics."
        )

    if decline_count > improvement_count:
        return (
            "The scenario produces an overall decline "
            f"across {decline_count} financial metrics."
        )

    return (
        "The scenario produces a balanced result with "
        f"{improvement_count} improvements, "
        f"{decline_count} declines, and "
        f"{unchanged_count} unchanged metrics."
    )


def build_scenario_comparison_report(
    result: ScenarioResult,
) -> ScenarioComparisonReport:
    """Build a comparison report from a scenario result."""
    comparisons = compare_snapshots(
        result.original_snapshot,
        result.projected_snapshot,
    )

    improvements = [
        comparison
        for comparison in comparisons
        if comparison.direction == ComparisonDirection.IMPROVEMENT
    ]

    declines = [
        comparison
        for comparison in comparisons
        if comparison.direction == ComparisonDirection.DECLINE
    ]

    unchanged = [
        comparison
        for comparison in comparisons
        if comparison.direction == ComparisonDirection.UNCHANGED
    ]

    summary = build_report_summary(
        improvement_count=len(improvements),
        decline_count=len(declines),
        unchanged_count=len(unchanged),
    )

    return ScenarioComparisonReport(
        scenario_name=result.name,
        scenario_type=result.scenario_type.value,
        summary=summary,
        comparisons=comparisons,
        improvements=improvements,
        declines=declines,
        unchanged=unchanged,
    )
