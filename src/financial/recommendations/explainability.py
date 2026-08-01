from src.financial.recommendations.models import Recommendation


def build_explanation(
    recommendation: Recommendation,
) -> dict:
    """Build structured explanation data."""

    return {
        "key": recommendation.key,
        "title": recommendation.title,
        "why": (
            recommendation.rationale
            if recommendation.rationale
            else recommendation.message
        ),
        "recommended_action": recommendation.action,
        "source_rule": recommendation.source_rule,
        "priority": recommendation.priority.name,
        "category": recommendation.category.value,
    }
