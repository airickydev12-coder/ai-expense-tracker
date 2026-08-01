from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from src.core.exceptions import ValidationError
from src.core.money import ZERO, to_money
from src.financial.scenarios.comparison import (
    METRIC_ACCOUNT_BALANCE,
    METRIC_GOAL_PROGRESS,
    METRIC_HEALTH_SCORE,
    METRIC_NET_CASH_FLOW,
    METRIC_NET_WORTH,
    METRIC_TOTAL_DEBT,
    MetricComparison,
)
from src.financial.scenarios.models import (
    ScenarioResult,
)
from src.financial.scenarios.plan import (
    ScenarioPlanResult,
)
from src.financial.scenarios.report import (
    ScenarioComparisonReport,
    build_scenario_comparison_report,
)

MIN_SCORE = 0.0
MAX_SCORE = 100.0


class RiskLevel(Enum):
    """Overall risk classification for a financial plan."""

    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class SustainabilityLevel(Enum):
    """Sustainability classification for a financial plan."""

    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"


class PlanRating(Enum):
    """Overall qualitative rating for a scored plan."""

    EXCELLENT = "Excellent"
    VERY_GOOD = "Very Good"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"


@dataclass(frozen=True)
class ScoreComponent:
    """Represents one component of a scenario score."""

    name: str
    score: float
    weight: float
    weighted_score: float
    explanation: str

    def __post_init__(self) -> None:
        """Validate and normalize the score component."""
        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValidationError("Score component name cannot be empty.")

        if self.score < MIN_SCORE or self.score > MAX_SCORE:
            raise ValidationError("Score component score must be between 0 and 100.")

        if self.weight < 0 or self.weight > 1:
            raise ValidationError("Score component weight must be between 0 and 1.")

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )

        object.__setattr__(
            self,
            "explanation",
            self.explanation.strip(),
        )

    @classmethod
    def create(
        cls,
        *,
        name: str,
        score: float,
        weight: float,
        explanation: str = "",
    ) -> "ScoreComponent":
        """Create a component and calculate its weighted score."""
        normalized_score = clamp_score(score)

        return cls(
            name=name,
            score=normalized_score,
            weight=weight,
            weighted_score=(normalized_score * weight),
            explanation=explanation,
        )

    def to_dict(self) -> dict:
        """Convert the score component to a dictionary."""
        return {
            "name": self.name,
            "score": self.score,
            "weight": self.weight,
            "weighted_score": self.weighted_score,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class ScenarioScore:
    """Represents the complete score for a scenario or plan."""

    name: str
    overall_score: float
    rating: PlanRating
    risk_level: RiskLevel
    sustainability: SustainabilityLevel
    components: list[ScoreComponent]
    strengths: list[str]
    concerns: list[str]
    recommendation: str

    def __post_init__(self) -> None:
        """Validate and protect mutable score data."""
        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValidationError("Scenario score name cannot be empty.")

        if self.overall_score < MIN_SCORE or self.overall_score > MAX_SCORE:
            raise ValidationError("Overall score must be between 0 and 100.")

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )
        object.__setattr__(
            self,
            "components",
            self.components.copy(),
        )
        object.__setattr__(
            self,
            "strengths",
            _clean_strings(self.strengths),
        )
        object.__setattr__(
            self,
            "concerns",
            _clean_strings(self.concerns),
        )
        object.__setattr__(
            self,
            "recommendation",
            self.recommendation.strip(),
        )

    def get_component(
        self,
        name: str,
    ) -> ScoreComponent | None:
        """Return a score component by name."""
        normalized_name = name.strip().lower()

        for component in self.components:
            if component.name.lower() == normalized_name:
                return component

        return None

    def to_dict(self) -> dict:
        """Convert the complete score to a dictionary."""
        return {
            "name": self.name,
            "overall_score": self.overall_score,
            "rating": self.rating.value,
            "risk_level": self.risk_level.value,
            "sustainability": self.sustainability.value,
            "components": [component.to_dict() for component in self.components],
            "strengths": self.strengths.copy(),
            "concerns": self.concerns.copy(),
            "recommendation": self.recommendation,
        }


def clamp_score(
    score: Decimal | float,
) -> float:
    """Clamp a score to the supported range."""
    return max(
        MIN_SCORE,
        min(float(score), MAX_SCORE),
    )


def classify_plan_rating(
    score: float,
) -> PlanRating:
    """Convert a numeric score into a plan rating."""
    normalized_score = clamp_score(score)

    if normalized_score >= 90:
        return PlanRating.EXCELLENT

    if normalized_score >= 80:
        return PlanRating.VERY_GOOD

    if normalized_score >= 70:
        return PlanRating.GOOD

    if normalized_score >= 60:
        return PlanRating.FAIR

    return PlanRating.POOR


def classify_risk_level(
    *,
    risk_count: int,
    conflict_count: int = 0,
    projected_cash_flow: Decimal | None = None,
) -> RiskLevel:
    """Classify risk from risks, conflicts, and projected cash flow."""
    if conflict_count >= 2 or (
        projected_cash_flow is not None and projected_cash_flow < 0
    ):
        return RiskLevel.CRITICAL

    if conflict_count == 1 or risk_count >= 4:
        return RiskLevel.HIGH

    if risk_count >= 2:
        return RiskLevel.MODERATE

    return RiskLevel.LOW


def classify_sustainability(
    *,
    projected_cash_flow: Decimal,
    original_cash_flow: Decimal,
    conflict_count: int,
) -> SustainabilityLevel:
    """Classify whether a scenario is financially sustainable."""
    if projected_cash_flow < 0:
        return SustainabilityLevel.POOR

    if conflict_count > 0:
        return SustainabilityLevel.FAIR

    if projected_cash_flow >= original_cash_flow:
        return SustainabilityLevel.EXCELLENT

    if projected_cash_flow >= (original_cash_flow * Decimal("0.75")):
        return SustainabilityLevel.GOOD

    return SustainabilityLevel.FAIR


def _get_comparison(
    report: ScenarioComparisonReport,
    metric: str,
) -> MetricComparison | None:
    """Return a comparison from a scenario report."""
    return report.get_comparison(metric)


def _score_positive_change(
    change: Decimal,
    reference_value: Decimal,
) -> float:
    """Score a change where larger positive values are beneficial."""
    if reference_value == 0:
        if change > 0:
            return 100.0

        if change < 0:
            return 0.0

        return 50.0

    percentage_change = change / abs(reference_value) * 100

    return clamp_score(50 + percentage_change * 2)


def _score_debt_change(
    change: Decimal,
    original_debt: Decimal,
) -> float:
    """Score total-debt change where a reduction is beneficial."""
    if original_debt <= 0:
        return 100.0

    debt_reduction = max(
        -change,
        Decimal("0"),
    )

    reduction_percentage = debt_reduction / original_debt * 100

    if change > 0:
        increase_percentage = change / original_debt * 100

        return clamp_score(50 - increase_percentage * 2)

    return clamp_score(50 + reduction_percentage * 2)


def score_net_worth(
    report: ScenarioComparisonReport,
) -> float:
    """Score projected net-worth change."""
    comparison = _get_comparison(
        report,
        METRIC_NET_WORTH,
    )

    if comparison is None:
        return 50.0

    return _score_positive_change(
        comparison.change,
        comparison.original_value,
    )


def score_cash_flow(
    report: ScenarioComparisonReport,
) -> float:
    """Score projected net cash-flow change."""
    comparison = _get_comparison(
        report,
        METRIC_NET_CASH_FLOW,
    )

    if comparison is None:
        return 50.0

    if comparison.projected_value < 0:
        return 0.0

    return _score_positive_change(
        comparison.change,
        comparison.original_value,
    )


def score_debt_improvement(
    report: ScenarioComparisonReport,
) -> float:
    """Score projected total-debt change."""
    comparison = _get_comparison(
        report,
        METRIC_TOTAL_DEBT,
    )

    if comparison is None:
        return 50.0

    return _score_debt_change(
        comparison.change,
        comparison.original_value,
    )


def score_savings_growth(
    report: ScenarioComparisonReport,
) -> float:
    """Score growth in account balances and goal progress."""
    account_comparison = _get_comparison(
        report,
        METRIC_ACCOUNT_BALANCE,
    )
    goal_comparison = _get_comparison(
        report,
        METRIC_GOAL_PROGRESS,
    )

    component_scores: list[float] = []

    if account_comparison is not None:
        component_scores.append(
            _score_positive_change(
                account_comparison.change,
                account_comparison.original_value,
            )
        )

    if goal_comparison is not None:
        component_scores.append(
            _score_positive_change(
                goal_comparison.change,
                goal_comparison.original_value,
            )
        )

    if not component_scores:
        return 50.0

    return sum(component_scores) / len(component_scores)


def score_financial_health(
    report: ScenarioComparisonReport,
) -> float:
    """Score projected financial-health improvement."""
    comparison = _get_comparison(
        report,
        METRIC_HEALTH_SCORE,
    )

    if comparison is None:
        return 50.0

    projected_score = clamp_score(comparison.projected_value)

    change_bonus = clamp_score(50 + comparison.change * 5)

    return projected_score * 0.7 + change_bonus * 0.3


def score_improvement_balance(
    report: ScenarioComparisonReport,
) -> float:
    """Score the balance of improvements and declines."""
    total_count = len(report.comparisons)

    if total_count == 0:
        return 50.0

    improvement_points = len(report.improvements) * 100
    unchanged_points = len(report.unchanged) * 50

    return (improvement_points + unchanged_points) / total_count


def score_risk(
    *,
    risk_count: int,
    conflict_count: int,
    projected_cash_flow: Decimal,
) -> float:
    """Score risk, where higher scores represent lower risk."""
    score = 100.0

    score -= risk_count * 10
    score -= conflict_count * 25

    if projected_cash_flow < 0:
        score -= 50

    return clamp_score(score)


def _clean_strings(
    values: list[str],
) -> list[str]:
    """Remove blank and duplicate strings."""
    cleaned: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = value.strip()

        if not normalized:
            continue

        key = normalized.lower()

        if key in seen:
            continue

        seen.add(key)
        cleaned.append(normalized)

    return cleaned


def _build_strengths(
    report: ScenarioComparisonReport,
) -> list[str]:
    """Build strengths from improved metrics."""
    return [
        (f"{comparison.metric} improves by " f"{comparison.change:+,.2f}.")
        for comparison in report.improvements
    ]


def _build_concerns(
    report: ScenarioComparisonReport,
    risks: list[str],
    conflicts: list[str],
) -> list[str]:
    """Build concerns from declines, risks, and conflicts."""
    concerns = [
        (f"{comparison.metric} declines by " f"{abs(comparison.change):,.2f}.")
        for comparison in report.declines
    ]

    concerns.extend(risks)
    concerns.extend(conflicts)

    return _clean_strings(concerns)


def _build_recommendation(
    score: float,
    risk_level: RiskLevel,
) -> str:
    """Build a recommendation based on score and risk."""
    if risk_level == RiskLevel.CRITICAL:
        return (
            "This plan is not recommended in its current form. "
            "Revise the plan before implementation because "
            "the projected financial risk is critical."
        )

    if score >= 90:
        return (
            "This plan is strongly recommended based on its "
            "projected financial improvements and manageable risk."
        )

    if score >= 75:
        return (
            "This plan is recommended, but its assumptions should "
            "be reviewed before implementation."
        )

    if score >= 60:
        return (
            "This plan may be useful, but it should be adjusted "
            "to improve its financial impact or sustainability."
        )

    return "This plan is not recommended in its current form."


def _calculate_score(
    *,
    name: str,
    report: ScenarioComparisonReport,
    original_snapshot: dict,
    projected_snapshot: dict,
    risks: list[str],
    conflicts: list[str],
) -> ScenarioScore:
    """Calculate the complete score for a scenario or plan."""
    original_cash_flow = to_money(
        original_snapshot.get(
            "net_cash_flow",
            ZERO,
        )
    )
    projected_cash_flow = to_money(
        projected_snapshot.get(
            "net_cash_flow",
            ZERO,
        )
    )

    components = [
        ScoreComponent.create(
            name="Net Worth Growth",
            score=score_net_worth(report),
            weight=0.25,
            explanation=("Measures projected improvement in net worth."),
        ),
        ScoreComponent.create(
            name="Cash Flow",
            score=score_cash_flow(report),
            weight=0.20,
            explanation=("Measures projected monthly cash-flow strength."),
        ),
        ScoreComponent.create(
            name="Debt Improvement",
            score=score_debt_improvement(report),
            weight=0.15,
            explanation=("Measures projected reduction in total debt."),
        ),
        ScoreComponent.create(
            name="Savings Growth",
            score=score_savings_growth(report),
            weight=0.15,
            explanation=("Measures growth in account balances and goals."),
        ),
        ScoreComponent.create(
            name="Financial Health",
            score=score_financial_health(report),
            weight=0.10,
            explanation=("Measures improvement in the financial-health score."),
        ),
        ScoreComponent.create(
            name="Improvement Balance",
            score=score_improvement_balance(report),
            weight=0.05,
            explanation=("Rewards plans with more improvements than declines."),
        ),
        ScoreComponent.create(
            name="Risk and Sustainability",
            score=score_risk(
                risk_count=len(risks),
                conflict_count=len(conflicts),
                projected_cash_flow=projected_cash_flow,
            ),
            weight=0.10,
            explanation=("Measures affordability, conflicts, and identified risks."),
        ),
    ]

    overall_score = clamp_score(
        sum(component.weighted_score for component in components)
    )

    risk_level = classify_risk_level(
        risk_count=len(risks),
        conflict_count=len(conflicts),
        projected_cash_flow=projected_cash_flow,
    )

    sustainability = classify_sustainability(
        projected_cash_flow=projected_cash_flow,
        original_cash_flow=original_cash_flow,
        conflict_count=len(conflicts),
    )

    return ScenarioScore(
        name=name,
        overall_score=round(
            overall_score,
            2,
        ),
        rating=classify_plan_rating(overall_score),
        risk_level=risk_level,
        sustainability=sustainability,
        components=components,
        strengths=_build_strengths(report),
        concerns=_build_concerns(
            report,
            risks,
            conflicts,
        ),
        recommendation=_build_recommendation(
            overall_score,
            risk_level,
        ),
    )


def score_scenario_result(
    result: ScenarioResult,
) -> ScenarioScore:
    """Score an individual scenario result."""
    report = build_scenario_comparison_report(result)

    return _calculate_score(
        name=result.name,
        report=report,
        original_snapshot=result.original_snapshot,
        projected_snapshot=result.projected_snapshot,
        risks=result.risks,
        conflicts=[],
    )


def score_scenario_plan(
    plan: ScenarioPlanResult,
) -> ScenarioScore:
    """Score a combined scenario plan."""
    report = ScenarioComparisonReport(
        scenario_name=plan.name,
        scenario_type="Combined Plan",
        summary=plan.cumulative_report.summary,
        comparisons=(plan.cumulative_report.comparisons),
        improvements=(plan.cumulative_report.improvements),
        declines=(plan.cumulative_report.declines),
        unchanged=(plan.cumulative_report.unchanged),
    )

    return _calculate_score(
        name=plan.name,
        report=report,
        original_snapshot=plan.original_snapshot,
        projected_snapshot=plan.projected_snapshot,
        risks=plan.risks,
        conflicts=plan.conflicts,
    )
