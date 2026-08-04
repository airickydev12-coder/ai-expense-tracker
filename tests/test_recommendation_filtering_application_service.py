"""Tests for recommendation filtering in the application service."""

import pytest

from src.financial.application import (
    recommendation_application_service as recommendation_service,
)
from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority


def make_recommendations() -> list[Recommendation]:
    """Create recommendations with different priorities and categories."""

    return [
        Recommendation(
            priority=RecommendationPriority.LOW,
            category=RecommendationCategory.BUDGET,
            title="Review subscription expenses",
            message="Review recurring subscription charges.",
            action="Cancel subscriptions you no longer use.",
            source_rule="SubscriptionReviewRule",
        ),
        Recommendation(
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.SAVINGS,
            title="Build emergency savings",
            message="Your emergency savings are below target.",
            action="Create an automatic savings transfer.",
            source_rule="EmergencySavingsRule",
        ),
        Recommendation(
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.BUDGET,
            title="Reduce dining expenses",
            message="Dining expenses are above your target.",
            action="Set a weekly dining limit.",
            source_rule="DiningSpendingRule",
        ),
    ]


@pytest.fixture
def generated_recommendations(
    monkeypatch: pytest.MonkeyPatch,
) -> list[Recommendation]:
    """Replace snapshot and generation dependencies with test data."""

    recommendations = make_recommendations()

    monkeypatch.setattr(
        recommendation_service,
        "build_financial_snapshot",
        lambda user_id: {"snapshot": "financial"},
    )

    monkeypatch.setattr(
        recommendation_service,
        "build_rule_snapshot",
        lambda snapshot: {"snapshot": "rules"},
    )

    monkeypatch.setattr(
        recommendation_service,
        "generate_recommendations",
        lambda user_id, snapshot: recommendations.copy(),
    )

    return recommendations


def test_build_recommendations_filters_by_priority(
    generated_recommendations: list[Recommendation],
) -> None:
    """Return recommendations matching the requested priority."""

    recommendations = recommendation_service.build_recommendations(
        1,
        priority="HIGH",
    )

    assert len(recommendations) == 2

    assert all(
        recommendation.priority.name == "HIGH" for recommendation in recommendations
    )


def test_build_recommendations_filters_by_category(
    generated_recommendations: list[Recommendation],
) -> None:
    """Return recommendations matching the requested category."""

    recommendations = recommendation_service.build_recommendations(
        1,
        category="Budget",
    )

    assert len(recommendations) == 2

    assert all(
        recommendation.category.value == "Budget" for recommendation in recommendations
    )


def test_build_recommendations_combines_filters(
    generated_recommendations: list[Recommendation],
) -> None:
    """Require both filters to match when both are supplied."""

    recommendations = recommendation_service.build_recommendations(
        1,
        priority="HIGH",
        category="Budget",
    )

    assert len(recommendations) == 1
    assert recommendations[0].key == "budget:reduce_dining_expenses"


def test_build_recommendations_applies_limit_after_filtering(
    generated_recommendations: list[Recommendation],
) -> None:
    """Apply the result limit after filtering recommendations."""

    recommendations = recommendation_service.build_recommendations(
        1,
        priority="HIGH",
        limit=1,
    )

    assert len(recommendations) == 1
    assert recommendations[0].priority.name == "HIGH"
    assert recommendations[0].key == "savings:build_emergency_savings"


def test_build_recommendations_filters_case_insensitively(
    generated_recommendations: list[Recommendation],
) -> None:
    """Normalize filter values used outside the API layer."""

    recommendations = recommendation_service.build_recommendations(
        1,
        priority=" high ",
        category=" budget ",
    )

    assert len(recommendations) == 1
    assert recommendations[0].key == "budget:reduce_dining_expenses"


def test_build_recommendations_returns_empty_for_invalid_limit(
    generated_recommendations: list[Recommendation],
) -> None:
    """Return no recommendations for a non-positive service limit."""

    recommendations = recommendation_service.build_recommendations(
        1,
        limit=0,
    )

    assert recommendations == []
