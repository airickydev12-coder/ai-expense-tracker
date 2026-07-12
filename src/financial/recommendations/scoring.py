from src.financial.recommendations.models import Recommendation


CATEGORY_WEIGHTS = {
    "Cash Flow": 40,
    "Income": 35,
    "Debt": 30,
    "Bills": 25,
    "Budget": 20,
    "Savings": 15,
    "Health": 15,
    "Expenses": 10,
    "Goals": 5,
    "Wealth": 0,
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