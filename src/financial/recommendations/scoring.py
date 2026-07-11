from src.financial.recommendations.models import Recommendation


def recommendation_score(
    recommendation: Recommendation,
) -> int:
    """
    Compute a sortable recommendation score.
    """
    return recommendation.priority.value * 100