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
    limit: int | None = None,
) -> list[Recommendation]:
    """
    Build financial recommendations from the current financial state.
    """

    financial_snapshot = build_financial_snapshot()

    rule_snapshot = build_rule_snapshot(financial_snapshot)

    return generate_recommendations(
        rule_snapshot,
        limit=limit,
    )


def get_recommendation_by_key(
    key: str,
) -> Recommendation | None:
    """
    Return a recommendation matching the supplied key.

    Returns None if no recommendation exists.
    """

    recommendations = build_recommendations()

    return next(
        (
            recommendation
            for recommendation in recommendations
            if recommendation.key == key
        ),
        None,
    )
