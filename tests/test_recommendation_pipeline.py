from src.financial.accounts import service as account_service
from src.financial.application.recommendation_application_service import (
    build_recommendations,
)
from src.financial.bills import service as bill_service
from src.financial.budgets import service as budget_service
from src.financial.debt import service as debt_service
from src.financial.expenses import service as expense_service
from src.financial.goals import service as goal_service
from src.financial.income import service as income_service

USER_ID = 1


def test_recommendation_pipeline_runs(monkeypatch):
    """The complete recommendation pipeline executes successfully."""

    monkeypatch.setattr(
        expense_service,
        "get_expenses",
        lambda user_id: [],
    )

    monkeypatch.setattr(
        budget_service,
        "get_budgets",
        lambda user_id: [],
    )

    monkeypatch.setattr(
        goal_service,
        "get_goals",
        lambda user_id: [],
    )

    monkeypatch.setattr(
        account_service,
        "get_accounts",
        lambda user_id: [],
    )

    monkeypatch.setattr(
        debt_service,
        "get_debts",
        lambda user_id: [],
    )

    monkeypatch.setattr(
        bill_service,
        "get_bills",
        lambda user_id: [],
    )

    monkeypatch.setattr(
        income_service,
        "get_income_entries",
        lambda user_id: [],
    )

    recommendations = build_recommendations(USER_ID)

    assert isinstance(recommendations, list)

    for recommendation in recommendations:
        assert recommendation.title
        assert recommendation.message
        assert recommendation.action
