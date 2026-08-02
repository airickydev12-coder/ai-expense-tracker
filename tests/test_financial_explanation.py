from src.financial.coach.advisor import (
    build_advice_from_ranked_scenario,
)
from src.financial.coach.explanation import (
    build_plain_language_explanation,
    explain_coaching_advice,
)
from src.financial.coach.models import (
    CoachingAdvice,
    CoachingPriority,
)
from src.financial.recommendations.category import RecommendationCategory
from src.financial.scenarios.models import (
    ScenarioAssumption,
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
    rank_scenarios,
)


def build_result() -> ScenarioResult:
    """Create a scenario result for explanation tests."""
    original = {
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

    return ScenarioResult(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Increase Income by 10%",
        description="",
        assumptions=[
            ScenarioAssumption(
                name="Increase Percentage",
                value=10,
                description="Projected income increase.",
            )
        ],
        original_snapshot=original,
        projected_snapshot={
            **original,
            "total_income": 5500,
            "net_cash_flow": 2500,
            "net_worth": 6500,
            "health_score": 82,
        },
        impacts=[],
        risks=["The income increase is not guaranteed."],
    )


def build_advice() -> CoachingAdvice:
    """Create coaching advice from the scenario."""
    ranked = rank_scenarios(
        [build_result()],
        ScenarioRankingMetric.OVERALL,
    )[0]

    return build_advice_from_ranked_scenario(ranked)


def test_explain_coaching_advice():
    explanation = explain_coaching_advice(
        build_advice(),
        build_result(),
    )

    assert explanation.advice_key
    assert "recommended" in (explanation.summary.lower())
    assert explanation.projected_effects
    assert any("Net Worth" in effect for effect in explanation.projected_effects)
    assert explanation.assumptions == ["Increase Percentage: 10"]
    assert explanation.risks


def test_build_plain_language_explanation():
    output = build_plain_language_explanation(build_advice())

    assert "Why this matters:" in output
    assert "Recommended action:" in output
    assert "Expected impact:" in output


def test_plain_language_explanation_includes_warnings():
    advice = CoachingAdvice(
        key="test:warning",
        title="Review Cash Flow",
        message="Cash flow requires attention.",
        action="Reduce discretionary spending.",
        reason="Projected cash flow is negative.",
        priority=CoachingPriority.CRITICAL,
        category=RecommendationCategory.CASH_FLOW,
        warnings=["The current plan is not sustainable."],
    )

    output = build_plain_language_explanation(advice)

    assert "Important considerations:" in output
    assert "The current plan is not sustainable." in output


def test_advice_explanation_serialization():
    explanation = explain_coaching_advice(
        build_advice(),
        build_result(),
    )

    data = explanation.to_dict()

    assert data["advice_key"]
    assert data["projected_effects"]
    assert data["assumptions"]
    assert data["risks"]
