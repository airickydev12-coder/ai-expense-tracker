from dataclasses import dataclass, field
from decimal import Decimal

from src.core.exceptions import ValidationError
from src.financial.scenarios.comparison import (
    ComparisonDirection,
    MetricComparison,
    compare_snapshots,
)
from src.financial.scenarios.models import (
    ScenarioRequest,
    ScenarioResult,
)
from src.financial.scenarios.report import (
    build_report_summary,
)


@dataclass(frozen=True)
class ScenarioPlanStep:
    """Represents one completed step in a scenario plan."""

    order: int
    request: ScenarioRequest
    result: ScenarioResult

    def __post_init__(self) -> None:
        """Validate the plan-step order."""
        if self.order <= 0:
            raise ValidationError("Scenario plan step order must be greater than zero.")

    def to_dict(self) -> dict:
        """Convert the plan step to a dictionary."""
        return {
            "order": self.order,
            "request": self.request.to_dict(),
            "result": self.result.to_dict(),
        }


@dataclass(frozen=True)
class CumulativeScenarioReport:
    """Represents cumulative changes across a scenario plan."""

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
        """Return one cumulative comparison by metric name."""
        normalized_metric = metric.strip().lower()

        for comparison in self.comparisons:
            if comparison.metric.lower() == normalized_metric:
                return comparison

        return None

    def to_dict(self) -> dict:
        """Convert the cumulative report to a dictionary."""
        return {
            "summary": self.summary,
            "comparisons": [comparison.to_dict() for comparison in self.comparisons],
            "improvements": [comparison.to_dict() for comparison in self.improvements],
            "declines": [comparison.to_dict() for comparison in self.declines],
            "unchanged": [comparison.to_dict() for comparison in self.unchanged],
        }


@dataclass(frozen=True)
class ScenarioPlanResult:
    """Represents the result of a combined financial plan."""

    name: str
    description: str
    original_snapshot: dict
    projected_snapshot: dict
    steps: list[ScenarioPlanStep]
    cumulative_report: CumulativeScenarioReport
    conflicts: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate and protect mutable plan data."""
        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValidationError("Scenario plan name cannot be empty.")

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )
        object.__setattr__(
            self,
            "description",
            self.description.strip(),
        )
        object.__setattr__(
            self,
            "original_snapshot",
            self.original_snapshot.copy(),
        )
        object.__setattr__(
            self,
            "projected_snapshot",
            self.projected_snapshot.copy(),
        )
        object.__setattr__(
            self,
            "steps",
            self.steps.copy(),
        )
        object.__setattr__(
            self,
            "conflicts",
            _clean_strings(self.conflicts),
        )
        object.__setattr__(
            self,
            "benefits",
            _clean_strings(self.benefits),
        )
        object.__setattr__(
            self,
            "risks",
            _clean_strings(self.risks),
        )
        object.__setattr__(
            self,
            "recommendations",
            _clean_strings(self.recommendations),
        )

    def get_step(
        self,
        order: int,
    ) -> ScenarioPlanStep | None:
        """Return a plan step by its order."""
        for step in self.steps:
            if step.order == order:
                return step

        return None

    def get_metric_change(
        self,
        metric: str,
    ) -> Decimal:
        """Return a cumulative metric change."""
        comparison = self.cumulative_report.get_comparison(metric)

        if comparison is None:
            return Decimal("0")

        return comparison.change

    def to_dict(self) -> dict:
        """Convert the complete plan result to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "original_snapshot": (self.original_snapshot.copy()),
            "projected_snapshot": (self.projected_snapshot.copy()),
            "steps": [step.to_dict() for step in self.steps],
            "cumulative_report": (self.cumulative_report.to_dict()),
            "conflicts": self.conflicts.copy(),
            "benefits": self.benefits.copy(),
            "risks": self.risks.copy(),
            "recommendations": (self.recommendations.copy()),
        }


def _clean_strings(
    values: list[str],
) -> list[str]:
    """Normalize, remove blanks, and deduplicate strings."""
    cleaned: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = value.strip()

        if not normalized:
            continue

        comparison_key = normalized.lower()

        if comparison_key in seen:
            continue

        seen.add(comparison_key)
        cleaned.append(normalized)

    return cleaned


def build_cumulative_scenario_report(
    original_snapshot: dict,
    projected_snapshot: dict,
) -> CumulativeScenarioReport:
    """Compare the original and final projected snapshots."""
    comparisons = compare_snapshots(
        original_snapshot,
        projected_snapshot,
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

    return CumulativeScenarioReport(
        summary=summary,
        comparisons=comparisons,
        improvements=improvements,
        declines=declines,
        unchanged=unchanged,
    )
