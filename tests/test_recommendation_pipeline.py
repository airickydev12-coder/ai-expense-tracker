from src.financial.application.recommendation_application_service import (
    build_recommendations,
)
from src.financial.budgets import service as budget_service
from src.financial.expenses import service as expense_service
from src.financial.goals import service as goal_service


def test_recommendation_pipeline_runs(monkeypatch):
    """The complete recommendation pipeline executes successfully."""

    monkeypatch.setattr(
        expense_service,
        "get_expenses",
        lambda: [],
    )

    monkeypatch.setattr(
        budget_service,
        "get_budgets",
        lambda: [],
    )

    monkeypatch.setattr(
        goal_service,
        "get_goals",
        lambda: [],
    )

    recommendations = build_recommendations()

    assert isinstance(recommendations, list)

    for recommendation in recommendations:
        assert recommendation.title
        assert recommendation.message
        assert recommendation.action
