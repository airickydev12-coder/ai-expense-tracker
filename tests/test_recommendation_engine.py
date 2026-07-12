from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.engine import RecommendationEngine
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority


def build_recommendations() -> list[Recommendation]:
    """Create recommendations for recommendation-engine tests."""
    return [
        Recommendation(
            priority=RecommendationPriority.LOW,
            category=RecommendationCategory.WEALTH,
            title="Invest Excess Cash",
            message="You have excess cash available.",
            action="Consider long-term investing.",
        ),
        Recommendation(
            priority=RecommendationPriority.CRITICAL,
            category=RecommendationCategory.CASH_FLOW,
            title="Negative Cash Flow",
            message="Your expenses exceed your income.",
            action="Reduce spending or increase income.",
        ),
        Recommendation(
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.DEBT,
            title="High Interest Debt",
            message="You have high-interest debt.",
            action="Prioritize repayment.",
        ),
        Recommendation(
            priority=RecommendationPriority.MEDIUM,
            category=RecommendationCategory.DEBT,
            title="Missing Minimum Payment",
            message="A debt has no minimum payment configured.",
            action="Add a minimum payment.",
        ),
    ]


def test_prioritize_recommendations():
    engine = RecommendationEngine()

    prioritized = engine.prioritize(build_recommendations())

    assert prioritized[0].priority == RecommendationPriority.CRITICAL
    assert prioritized[1].priority == RecommendationPriority.HIGH
    assert prioritized[2].priority == RecommendationPriority.MEDIUM
    assert prioritized[3].priority == RecommendationPriority.LOW


def test_group_recommendations_by_category():
    engine = RecommendationEngine()

    grouped = engine.group_by_category(build_recommendations())

    assert len(grouped[RecommendationCategory.DEBT]) == 2
    assert len(grouped[RecommendationCategory.CASH_FLOW]) == 1
    assert len(grouped[RecommendationCategory.WEALTH]) == 1


def test_top_n_recommendations():
    engine = RecommendationEngine()

    top_recommendations = engine.top_n(
        build_recommendations(),
        limit=2,
    )

    assert len(top_recommendations) == 2
    assert top_recommendations[0].priority == RecommendationPriority.CRITICAL
    assert top_recommendations[1].priority == RecommendationPriority.HIGH


def test_top_n_with_zero_limit():
    engine = RecommendationEngine()

    assert engine.top_n(build_recommendations(), limit=0) == []


def test_deduplicate_keeps_one_recommendation_per_key():
    engine = RecommendationEngine()

    recommendations = [
        Recommendation(
            priority=RecommendationPriority.MEDIUM,
            category=RecommendationCategory.DEBT,
            title="High Interest Debt",
            message="First message.",
            action="First action.",
        ),
        Recommendation(
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.DEBT,
            title="High Interest Debt",
            message="Higher-priority message.",
            action="Higher-priority action.",
        ),
    ]

    results = engine.deduplicate(recommendations)

    assert len(results) == 1
    assert results[0].priority == RecommendationPriority.HIGH
    assert results[0].message == "Higher-priority message."


def test_recommendation_has_stable_key():
    recommendation = Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.DEBT,
        title="High Interest Debt",
        message="You have high-interest debt.",
        action="Prioritize repayment.",
    )

    assert recommendation.key == "debt:high_interest_debt"


def test_recommendation_serialization_includes_metadata():
    recommendation = Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.DEBT,
        title="High Interest Debt",
        message="You have high-interest debt.",
        action="Prioritize repayment.",
        rationale="Interest charges increase the repayment cost.",
        source_rule="HighInterestDebtRule",
    )

    data = recommendation.to_dict()

    assert data["key"] == "debt:high_interest_debt"
    assert data["priority"] == "HIGH"
    assert data["category"] == "Debt"
    assert data["score"] == 300
    assert data["rationale"] == (
        "Interest charges increase the repayment cost."
    )
    assert data["source_rule"] == "HighInterestDebtRule"