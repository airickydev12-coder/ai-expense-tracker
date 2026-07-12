from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.explainability import (
    build_explanation,
)
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.cash_flow_rule import NegativeCashFlowRule
from src.financial.rules.rule_engine import RuleEngine


def test_rule_engine_sets_source_rule():
    engine = RuleEngine()
    engine.register(NegativeCashFlowRule())

    recommendations = engine.evaluate(
        {
            "net_cash_flow": -100,
        }
    )

    assert len(recommendations) == 1
    assert recommendations[0].source_rule == "NegativeCashFlowRule"


def test_explanation_uses_rationale():
    recommendation = Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.DEBT,
        title="High Interest Debt",
        message="High interest debt detected.",
        action="Pay it off.",
        rationale="Interest compounds quickly.",
        source_rule="HighInterestDebtRule",
    )

    explanation = build_explanation(
        recommendation
    )

    assert explanation["why"] == (
        "Interest compounds quickly."
    )


def test_explanation_falls_back_to_message():
    recommendation = Recommendation(
        priority=RecommendationPriority.MEDIUM,
        category=RecommendationCategory.BUDGET,
        title="Budget Warning",
        message="Budget nearly exhausted.",
        action="Reduce spending.",
    )

    explanation = build_explanation(
        recommendation
    )

    assert explanation["why"] == (
        "Budget nearly exhausted."
    )


def test_actionable_property():
    recommendation = Recommendation(
        priority=RecommendationPriority.LOW,
        category=RecommendationCategory.WEALTH,
        title="Invest",
        message="Cash available.",
        action="Invest excess cash.",
    )

    assert recommendation.is_actionable is True