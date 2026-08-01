from src.financial.recommendations.engine import RecommendationEngine
from src.financial.recommendations.history_service import (
    filter_displayable_recommendations,
)
from src.financial.recommendations.models import Recommendation
from src.financial.rules.rule_engine import create_default_rule_engine


def generate_recommendations(
    snapshot: dict,
    limit: int | None = None,
) -> list[Recommendation]:
    """Generate, process, and lifecycle-filter recommendations."""
    rule_engine = create_default_rule_engine()

    raw_recommendations = rule_engine.evaluate(snapshot)

    recommendation_engine = RecommendationEngine()

    processed_recommendations = recommendation_engine.process(raw_recommendations)

    displayable_recommendations = filter_displayable_recommendations(
        processed_recommendations
    )

    if limit is not None:
        if limit <= 0:
            return []

        return displayable_recommendations[:limit]

    return displayable_recommendations
