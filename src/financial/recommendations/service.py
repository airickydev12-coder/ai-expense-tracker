from src.financial.recommendations.engine import RecommendationEngine
from src.financial.recommendations.models import Recommendation
from src.financial.rules.rule_engine import create_default_rule_engine


def generate_recommendations(
    snapshot: dict,
    limit: int | None = None,
) -> list[Recommendation]:
    """Generate and process recommendations for a financial snapshot."""
    rule_engine = create_default_rule_engine()
    raw_recommendations = rule_engine.evaluate(snapshot)

    recommendation_engine = RecommendationEngine()
    processed_recommendations = recommendation_engine.process(
        raw_recommendations
    )

    if limit is not None:
        if limit <= 0:
            return []

        return processed_recommendations[:limit]

    return processed_recommendations