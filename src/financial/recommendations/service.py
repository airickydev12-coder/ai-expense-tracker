from src.financial.recommendations.engine import RecommendationEngine
from src.financial.recommendations.models import Recommendation
from src.financial.rules.rule_engine import (
    create_default_rule_engine,
)


def generate_recommendations(
    snapshot: dict,
    limit: int | None = None,
) -> list[Recommendation]:
    """
    Generate recommendations from the financial snapshot.
    """
    rule_engine = create_default_rule_engine()

    recommendations = rule_engine.evaluate(
        snapshot
    )

    engine = RecommendationEngine()

    recommendations = engine.process(
        recommendations
    )

    if limit is not None:
        return recommendations[:limit]

    return recommendations