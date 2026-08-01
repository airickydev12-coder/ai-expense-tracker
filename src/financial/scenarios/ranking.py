from dataclasses import dataclass
from enum import Enum

from src.core.exceptions import ValidationError
from src.financial.scenarios.models import (
    ScenarioResult,
)
from src.financial.scenarios.report import (
    ScenarioComparisonReport,
    build_scenario_comparison_report,
)
from src.financial.scenarios.scoring import (
    RiskLevel,
    ScenarioScore,
    SustainabilityLevel,
    score_scenario_result,
)


class ScenarioRankingMetric(Enum):
    """Supported metrics for ranking financial scenarios."""

    NET_WORTH = "Net Worth"
    CASH_FLOW = "Net Cash Flow"
    DEBT_REDUCTION = "Total Debt"
    IMPROVEMENT_COUNT = "Improvement Count"
    LOWEST_RISK = "Lowest Risk"
    SUSTAINABILITY = "Sustainability"
    OVERALL = "Overall"


@dataclass(frozen=True)
class RankedScenario:
    """Represents one ranked financial scenario."""

    rank: int
    scenario_name: str
    scenario_type: str
    score: float
    ranking_metric: ScenarioRankingMetric
    reason: str
    result: ScenarioResult
    report: ScenarioComparisonReport
    scenario_score: ScenarioScore

    def __post_init__(self) -> None:
        """Validate the ranked scenario."""
        if self.rank <= 0:
            raise ValidationError("Scenario rank must be greater than zero.")

        normalized_name = self.scenario_name.strip()

        if not normalized_name:
            raise ValidationError("Ranked scenario name cannot be empty.")

        object.__setattr__(
            self,
            "scenario_name",
            normalized_name,
        )

        object.__setattr__(
            self,
            "scenario_type",
            self.scenario_type.strip(),
        )

        object.__setattr__(
            self,
            "reason",
            self.reason.strip(),
        )

    def to_dict(self) -> dict:
        """Convert the ranked scenario to a dictionary."""
        return {
            "rank": self.rank,
            "scenario_name": self.scenario_name,
            "scenario_type": self.scenario_type,
            "score": self.score,
            "ranking_metric": self.ranking_metric.value,
            "reason": self.reason,
            "scenario_score": (self.scenario_score.to_dict()),
            "result": self.result.to_dict(),
            "report": self.report.to_dict(),
        }


def get_metric_change(
    report: ScenarioComparisonReport,
    metric: str,
) -> float:
    """Return the change for one comparison metric."""
    comparison = report.get_comparison(metric)

    if comparison is None:
        return 0.0

    return float(comparison.change)


def get_debt_reduction(
    report: ScenarioComparisonReport,
) -> float:
    """Return debt reduction as a positive value."""
    debt_change = get_metric_change(
        report,
        "Total Debt",
    )

    return max(
        -debt_change,
        0.0,
    )


def get_improvement_count(
    report: ScenarioComparisonReport,
) -> int:
    """Return the number of improved metrics."""
    return len(report.improvements)


def get_risk_ranking_score(
    risk_level: RiskLevel,
) -> float:
    """
    Return a ranking value for risk.

    Higher values represent lower financial risk.
    """
    scores = {
        RiskLevel.LOW: 4.0,
        RiskLevel.MODERATE: 3.0,
        RiskLevel.HIGH: 2.0,
        RiskLevel.CRITICAL: 1.0,
    }

    return scores[risk_level]


def get_sustainability_ranking_score(
    sustainability: SustainabilityLevel,
) -> float:
    """
    Return a ranking value for sustainability.

    Higher values represent stronger sustainability.
    """
    scores = {
        SustainabilityLevel.EXCELLENT: 4.0,
        SustainabilityLevel.GOOD: 3.0,
        SustainabilityLevel.FAIR: 2.0,
        SustainabilityLevel.POOR: 1.0,
    }

    return scores[sustainability]


def calculate_overall_score(
    report: ScenarioComparisonReport,
) -> float:
    """
    Calculate the legacy comparison-based ranking score.

    This function is preserved for compatibility with existing
    callers and tests. New overall rankings use ScenarioScore.
    """
    improvement_score = len(report.improvements) * 100
    decline_penalty = len(report.declines) * 100

    net_worth_change = get_metric_change(
        report,
        "Net Worth",
    )

    cash_flow_change = get_metric_change(
        report,
        "Net Cash Flow",
    )

    debt_reduction = get_debt_reduction(report)

    financial_impact_score = (
        net_worth_change / 1000 + cash_flow_change / 100 + debt_reduction / 1000
    )

    return improvement_score - decline_penalty + financial_impact_score


def calculate_ranking_score(
    report: ScenarioComparisonReport,
    ranking_metric: ScenarioRankingMetric,
    scenario_score: ScenarioScore | None = None,
) -> float:
    """Calculate a ranking score for one scenario."""
    if ranking_metric == ScenarioRankingMetric.NET_WORTH:
        return get_metric_change(
            report,
            "Net Worth",
        )

    if ranking_metric == ScenarioRankingMetric.CASH_FLOW:
        return get_metric_change(
            report,
            "Net Cash Flow",
        )

    if ranking_metric == ScenarioRankingMetric.DEBT_REDUCTION:
        return get_debt_reduction(report)

    if ranking_metric == ScenarioRankingMetric.IMPROVEMENT_COUNT:
        return float(get_improvement_count(report))

    if ranking_metric == ScenarioRankingMetric.LOWEST_RISK:
        if scenario_score is None:
            return 0.0

        return get_risk_ranking_score(scenario_score.risk_level)

    if ranking_metric == ScenarioRankingMetric.SUSTAINABILITY:
        if scenario_score is None:
            return 0.0

        return get_sustainability_ranking_score(scenario_score.sustainability)

    if scenario_score is not None:
        return scenario_score.overall_score

    return calculate_overall_score(report)


def build_ranking_reason(
    *,
    ranking_metric: ScenarioRankingMetric,
    score: float,
    report: ScenarioComparisonReport,
    scenario_score: ScenarioScore,
) -> str:
    """Build a concise explanation for a ranking."""
    if ranking_metric == ScenarioRankingMetric.NET_WORTH:
        return "Projected net-worth change: " f"{score:+,.2f}."

    if ranking_metric == ScenarioRankingMetric.CASH_FLOW:
        return "Projected monthly cash-flow change: " f"{score:+,.2f}."

    if ranking_metric == ScenarioRankingMetric.DEBT_REDUCTION:
        return "Projected debt reduction: " f"{score:,.2f}."

    if ranking_metric == ScenarioRankingMetric.IMPROVEMENT_COUNT:
        return f"{int(score)} compared financial metrics " "are projected to improve."

    if ranking_metric == ScenarioRankingMetric.LOWEST_RISK:
        return "Risk classification: " f"{scenario_score.risk_level.value}."

    if ranking_metric == ScenarioRankingMetric.SUSTAINABILITY:
        return (
            "Sustainability classification: " f"{scenario_score.sustainability.value}."
        )

    return (
        f"Overall plan score: "
        f"{scenario_score.overall_score:.2f}/100 "
        f"({scenario_score.rating.value})."
    )


def rank_scenarios(
    results: list[ScenarioResult],
    ranking_metric: ScenarioRankingMetric = (ScenarioRankingMetric.OVERALL),
) -> list[RankedScenario]:
    """Rank scenarios from strongest to weakest."""
    scored_results: list[
        tuple[
            ScenarioResult,
            ScenarioComparisonReport,
            ScenarioScore,
            float,
            str,
        ]
    ] = []

    for result in results:
        report = build_scenario_comparison_report(result)

        scenario_score = score_scenario_result(result)

        ranking_score = calculate_ranking_score(
            report,
            ranking_metric,
            scenario_score,
        )

        reason = build_ranking_reason(
            ranking_metric=ranking_metric,
            score=ranking_score,
            report=report,
            scenario_score=scenario_score,
        )

        scored_results.append(
            (
                result,
                report,
                scenario_score,
                ranking_score,
                reason,
            )
        )

    scored_results.sort(
        key=lambda item: (
            -item[3],
            -item[2].overall_score,
            item[0].name.lower(),
            item[0].scenario_type.value.lower(),
        )
    )

    ranked: list[RankedScenario] = []

    for index, (
        result,
        report,
        scenario_score,
        ranking_score,
        reason,
    ) in enumerate(
        scored_results,
        start=1,
    ):
        ranked.append(
            RankedScenario(
                rank=index,
                scenario_name=result.name,
                scenario_type=(result.scenario_type.value),
                score=round(
                    ranking_score,
                    2,
                ),
                ranking_metric=ranking_metric,
                reason=reason,
                result=result,
                report=report,
                scenario_score=scenario_score,
            )
        )

    return ranked


def get_best_scenario(
    results: list[ScenarioResult],
    ranking_metric: ScenarioRankingMetric = (ScenarioRankingMetric.OVERALL),
) -> RankedScenario | None:
    """Return the highest-ranked scenario."""
    ranked = rank_scenarios(
        results,
        ranking_metric,
    )

    if not ranked:
        return None

    return ranked[0]


def get_safest_scenario(
    results: list[ScenarioResult],
) -> RankedScenario | None:
    """Return the scenario with the lowest risk."""
    return get_best_scenario(
        results,
        ScenarioRankingMetric.LOWEST_RISK,
    )


def get_most_sustainable_scenario(
    results: list[ScenarioResult],
) -> RankedScenario | None:
    """Return the scenario with the best sustainability."""
    return get_best_scenario(
        results,
        ScenarioRankingMetric.SUSTAINABILITY,
    )
