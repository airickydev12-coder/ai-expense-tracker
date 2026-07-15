from dataclasses import dataclass
from enum import Enum

from src.financial.scenarios.comparison import (
    ComparisonDirection,
)
from src.financial.scenarios.models import ScenarioResult
from src.financial.scenarios.report import (
    ScenarioComparisonReport,
    build_scenario_comparison_report,
)


class ScenarioRankingMetric(Enum):
    """Supported metrics for ranking financial scenarios."""

    NET_WORTH = "Net Worth"
    CASH_FLOW = "Net Cash Flow"
    DEBT_REDUCTION = "Total Debt"
    IMPROVEMENT_COUNT = "Improvement Count"
    OVERALL = "Overall"


@dataclass(frozen=True)
class RankedScenario:
    """Represents one scenario and its ranking score."""

    rank: int
    scenario_name: str
    scenario_type: str
    score: float
    ranking_metric: ScenarioRankingMetric
    result: ScenarioResult
    report: ScenarioComparisonReport

    def to_dict(self) -> dict:
        """Convert the ranked scenario to a dictionary."""
        return {
            "rank": self.rank,
            "scenario_name": self.scenario_name,
            "scenario_type": self.scenario_type,
            "score": self.score,
            "ranking_metric": self.ranking_metric.value,
            "result": self.result.to_dict(),
            "report": self.report.to_dict(),
        }


def get_metric_change(
    report: ScenarioComparisonReport,
    metric: str,
) -> float:
    """Return the change for a comparison metric."""
    comparison = report.get_comparison(metric)

    if comparison is None:
        return 0.0

    return comparison.change


def get_debt_reduction(
    report: ScenarioComparisonReport,
) -> float:
    """Return debt reduction as a positive ranking value."""
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
    """Return the number of improved financial metrics."""
    return len(report.improvements)


def calculate_overall_score(
    report: ScenarioComparisonReport,
) -> float:
    """
    Calculate a normalized composite scenario score.

    The score rewards improvements and penalizes declines.
    It also gives modest weight to net-worth, cash-flow,
    and debt improvements without allowing dollar values
    to overwhelm the metric-count signal.
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
) -> float:
    """Calculate a ranking score for one scenario report."""
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

    return calculate_overall_score(report)


def rank_scenarios(
    results: list[ScenarioResult],
    ranking_metric: ScenarioRankingMetric = (ScenarioRankingMetric.OVERALL),
) -> list[RankedScenario]:
    """Rank scenarios from strongest to weakest."""
    scored_results: list[
        tuple[
            ScenarioResult,
            ScenarioComparisonReport,
            float,
        ]
    ] = []

    for result in results:
        report = build_scenario_comparison_report(result)

        score = calculate_ranking_score(
            report,
            ranking_metric,
        )

        scored_results.append(
            (
                result,
                report,
                score,
            )
        )

    scored_results.sort(
        key=lambda item: (
            -item[2],
            item[0].name.lower(),
            item[0].scenario_type.value.lower(),
        )
    )

    ranked: list[RankedScenario] = []

    for index, (
        result,
        report,
        score,
    ) in enumerate(
        scored_results,
        start=1,
    ):
        ranked.append(
            RankedScenario(
                rank=index,
                scenario_name=result.name,
                scenario_type=(result.scenario_type.value),
                score=score,
                ranking_metric=ranking_metric,
                result=result,
                report=report,
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
