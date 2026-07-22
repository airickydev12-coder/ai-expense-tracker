from src.financial.application.financial_snapshot_service import (
    FinancialSnapshot,
)
from src.financial.application import (
    recommendation_application_service,
)
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import (
    RecommendationPriority,
)
from src.financial.recommendations.category import (
    RecommendationCategory,
)


def test_build_recommendations(monkeypatch):
    """Application service orchestrates the recommendation pipeline."""

    snapshot = FinancialSnapshot(
        total_expenses=100.0,
        average_expense=50.0,
        highest_expense=None,
        lowest_expense=None,
        category_totals={},
        budget_count=1,
        goal_count=1,
        health_score=80,
        health_status="Good",
    )

    recommendation = Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.HEALTH,
        title="Improve Health",
        message="Improve your financial health.",
        action="Review your spending.",
    )

    monkeypatch.setattr(
        recommendation_application_service,
        "build_financial_snapshot",
        lambda: snapshot,
    )

    monkeypatch.setattr(
        recommendation_application_service,
        "build_rule_snapshot",
        lambda snapshot: {"health_score": 80},
    )

    monkeypatch.setattr(
        recommendation_application_service,
        "generate_recommendations",
        lambda snapshot, limit=None: [recommendation],
    )

    results = recommendation_application_service.build_recommendations()

    assert len(results) == 1
    assert results[0].title == "Improve Health"
