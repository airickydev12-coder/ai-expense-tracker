from src.financial.coach.advisor import (
    build_advice_from_ranked_scenario,
    generate_optimizer_advice,
    get_top_optimizer_advice,
)
from src.financial.coach.models import (
    CoachingPriority,
)
from src.financial.recommendations.category import RecommendationCategory
from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.optimizer import (
    OptimizationResult,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
    rank_scenarios,
)


def build_snapshot() -> dict:
    """Create a baseline financial snapshot."""
    return {
        "total_income": 5000,
        "total_expenses": 3000,
        "net_cash_flow": 2000,
        "total_account_balance": 8000,
        "total_goal_progress": 2500,
        "total_debt": 10000,
        "net_worth": 500,
        "health_score": 70,
        "health_status": "Good",
    }


def build_income_result() -> ScenarioResult:
    """Create a strong optimizer scenario result."""
    original = build_snapshot()

    return ScenarioResult(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Increase Income by 10%",
        description="",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot={
            **original,
            "total_income": 5500,
            "net_cash_flow": 2500,
            "total_account_balance": 14000,
            "net_worth": 6500,
            "health_score": 82,
        },
        impacts=[],
        recommendations=["Direct part of the additional income to savings."],
    )


def build_optimizer_result() -> OptimizationResult:
    """Create a completed optimization result."""
    result = build_income_result()

    ranked = rank_scenarios(
        [result],
        ScenarioRankingMetric.OVERALL,
    )

    return OptimizationResult(
        snapshot=build_snapshot(),
        candidates=[],
        successful_results=[result],
        ranked_scenarios=ranked,
        failures=[],
        ranking_metric=(ScenarioRankingMetric.OVERALL),
    )


def test_build_advice_from_ranked_scenario():
    ranked = build_optimizer_result().ranked_scenarios[0]

    advice = build_advice_from_ranked_scenario(ranked)

    assert advice.title == "Increase Income by 10%"
    assert advice.category == RecommendationCategory.INCOME
    assert advice.priority in {
        CoachingPriority.HIGH,
        CoachingPriority.MEDIUM,
    }
    assert advice.score is not None
    assert "overall score" in advice.reason.lower()
    assert "net worth" in (advice.expected_impact.lower())


def test_generate_optimizer_advice():
    result = build_optimizer_result()

    advice = generate_optimizer_advice(result)

    assert len(advice) == 1
    assert advice[0].source_scenario == ("Increase Income by 10%")


def test_generate_optimizer_advice_respects_limit():
    result = build_optimizer_result()

    assert (
        generate_optimizer_advice(
            result,
            limit=0,
        )
        == []
    )


def test_get_top_optimizer_advice():
    advice = get_top_optimizer_advice(build_optimizer_result())

    assert advice is not None
    assert advice.title == "Increase Income by 10%"


def test_get_top_optimizer_advice_when_empty():
    result = OptimizationResult(
        snapshot=build_snapshot(),
        candidates=[],
        successful_results=[],
        ranked_scenarios=[],
        failures=[],
        ranking_metric=(ScenarioRankingMetric.OVERALL),
    )

    assert get_top_optimizer_advice(result) is None


def test_coaching_advice_serialization():
    ranked = build_optimizer_result().ranked_scenarios[0]

    advice = build_advice_from_ranked_scenario(ranked)

    data = advice.to_dict()

    assert data["title"] == "Increase Income by 10%"
    assert data["category"] == "Income"
    assert "priority" in data
    assert "expected_impact" in data
