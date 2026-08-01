from src.financial.recommendations.priority import RecommendationPriority
from src.financial.recommendations.service import generate_recommendations


def build_snapshot() -> dict:
    """Build a snapshot containing several recommendation triggers."""
    return {
        "total_income": 1000,
        "total_expenses": 2000,
        "net_cash_flow": -1000,
        "total_account_balance": 500,
        "total_goal_progress": 0,
        "total_debt": 3000,
        "net_worth": -2500,
        "budget_report": [],
        "health_score": 20,
        "health_status": "Critical",
        "accounts": [],
        "goals": [],
        "debts": [],
        "bills": [],
        "current_day": 10,
        "average_expense": 1000,
        "largest_expense": None,
        "category_totals": {},
    }


def test_generate_recommendations_returns_prioritized_results():
    recommendations = generate_recommendations(build_snapshot())

    assert recommendations
    assert all(
        recommendations[index].priority >= recommendations[index + 1].priority
        for index in range(len(recommendations) - 1)
    )


def test_generate_recommendations_applies_limit():
    recommendations = generate_recommendations(
        build_snapshot(),
        limit=2,
    )

    assert len(recommendations) == 2


def test_generate_recommendations_returns_recommendation_objects():
    recommendations = generate_recommendations(
        build_snapshot(),
        limit=1,
    )

    assert recommendations[0].priority == RecommendationPriority.CRITICAL
