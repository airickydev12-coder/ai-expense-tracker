"""Application service for generating financial recommendations."""

from src.financial.application.financial_snapshot_service import (
    build_financial_snapshot,
)
from src.financial.application.recommendation_snapshot_adapter import (
    build_rule_snapshot,
)
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.service import (
    generate_recommendations,
)


def build_recommendations(
    user_id: int,
    priority: str | None = None,
    category: str | None = None,
    limit: int | None = None,
) -> list[Recommendation]:
    """
    Build, filter, and limit recommendations from the current financial state.

    Filtering is applied before the result limit.
    """

    financial_snapshot = build_financial_snapshot(user_id)

    rule_snapshot = build_rule_snapshot(financial_snapshot)

    recommendations = generate_recommendations(user_id, rule_snapshot)

    if priority is not None:
        normalized_priority = priority.strip().upper()

        recommendations = [
            recommendation
            for recommendation in recommendations
            if recommendation.priority.name == normalized_priority
        ]

    if category is not None:
        normalized_category = category.strip().casefold()

        recommendations = [
            recommendation
            for recommendation in recommendations
            if (recommendation.category.value.casefold() == normalized_category)
        ]

    if limit is not None:
        if limit <= 0:
            return []

        recommendations = recommendations[:limit]

    return recommendations


def get_recommendation_by_key(
    user_id: int,
    key: str,
) -> Recommendation | None:
    """
    Return a recommendation matching the supplied key.

    Returns None if no recommendation exists.
    """

    recommendations = build_recommendations(user_id)

    return next(
        (
            recommendation
            for recommendation in recommendations
            if recommendation.key == key
        ),
        None,
    )
