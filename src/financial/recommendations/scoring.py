from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation

CATEGORY_WEIGHTS = {
    RecommendationCategory.CASH_FLOW.value: 40,
    RecommendationCategory.INCOME.value: 35,
    RecommendationCategory.DEBT.value: 30,
    RecommendationCategory.BILLS.value: 25,
    RecommendationCategory.BUDGET.value: 20,
    RecommendationCategory.SAVINGS.value: 15,
    RecommendationCategory.HEALTH.value: 15,
    RecommendationCategory.EXPENSES.value: 10,
    RecommendationCategory.GOALS.value: 5,
    RecommendationCategory.WEALTH.value: 0,
}


def recommendation_score(
    recommendation: Recommendation,
) -> int:
    """Compute the recommendation's sortable intelligence score."""
    priority_score = recommendation.priority.value * 100
    category_score = CATEGORY_WEIGHTS.get(
        recommendation.category.value,
        0,
    )

    return priority_score + category_score
