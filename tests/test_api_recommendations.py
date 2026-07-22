"""Tests for the financial recommendations API."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routers import recommendations as recommendations_router
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority


client = TestClient(app)


def make_test_recommendation() -> Recommendation:
    """Create a recommendation used by API tests."""

    return Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.BUDGET,
        title="Reduce dining expenses",
        message="Dining expenses are above your target.",
        action="Set a weekly dining limit.",
        rationale="Dining represents a large share of spending.",
        source_rule="DiningSpendingRule",
    )


def test_get_recommendations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return serialized financial recommendations."""

    test_recommendations = [
        make_test_recommendation(),
    ]

    monkeypatch.setattr(
        recommendations_router,
        "build_recommendations",
        lambda priority=None, category=None, limit=None: (test_recommendations),
    )

    response = client.get("/recommendations")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0] == {
        "key": "budget:reduce_dining_expenses",
        "priority": "HIGH",
        "category": "Budget",
        "score": 300,
        "title": "Reduce dining expenses",
        "message": "Dining expenses are above your target.",
        "action": "Set a weekly dining limit.",
        "rationale": "Dining represents a large share of spending.",
        "source_rule": "DiningSpendingRule",
        "is_actionable": True,
    }


def test_get_recommendations_passes_filters_and_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pass filters and limit to the application service."""

    captured_arguments: dict[str, object] = {}

    def fake_build_recommendations(
        priority: str | None = None,
        category: str | None = None,
        limit: int | None = None,
    ) -> list[Recommendation]:
        captured_arguments["priority"] = priority
        captured_arguments["category"] = category
        captured_arguments["limit"] = limit

        return []

    monkeypatch.setattr(
        recommendations_router,
        "build_recommendations",
        fake_build_recommendations,
    )

    response = client.get(
        "/recommendations" "?priority=HIGH" "&category=Budget" "&limit=3"
    )

    assert response.status_code == 200
    assert response.json() == []

    assert captured_arguments == {
        "priority": "HIGH",
        "category": "Budget",
        "limit": 3,
    }


def test_get_recommendations_accepts_cash_flow_category(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Accept category values containing spaces."""

    captured_category: str | None = None

    def fake_build_recommendations(
        priority: str | None = None,
        category: str | None = None,
        limit: int | None = None,
    ) -> list[Recommendation]:
        nonlocal captured_category

        captured_category = category
        return []

    monkeypatch.setattr(
        recommendations_router,
        "build_recommendations",
        fake_build_recommendations,
    )

    response = client.get("/recommendations?category=Cash%20Flow")

    assert response.status_code == 200
    assert response.json() == []
    assert captured_category == "Cash Flow"


def test_get_recommendations_rejects_invalid_limit() -> None:
    """Reject recommendation limits below one."""

    response = client.get("/recommendations?limit=0")

    assert response.status_code == 422


def test_get_recommendations_rejects_invalid_priority() -> None:
    """Reject unsupported recommendation priorities."""

    response = client.get("/recommendations?priority=URGENT")

    assert response.status_code == 422


def test_get_recommendations_rejects_invalid_category() -> None:
    """Reject unsupported recommendation categories."""

    response = client.get("/recommendations?category=Shopping")

    assert response.status_code == 422


def test_get_recommendation_by_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return a recommendation matching the requested key."""

    recommendation = make_test_recommendation()

    monkeypatch.setattr(
        recommendations_router,
        "get_recommendation_by_key",
        lambda key: recommendation,
    )

    response = client.get("/recommendations/budget:reduce_dining_expenses")

    assert response.status_code == 200

    assert response.json() == {
        "key": "budget:reduce_dining_expenses",
        "priority": "HIGH",
        "category": "Budget",
        "score": 300,
        "title": "Reduce dining expenses",
        "message": "Dining expenses are above your target.",
        "action": "Set a weekly dining limit.",
        "rationale": "Dining represents a large share of spending.",
        "source_rule": "DiningSpendingRule",
        "is_actionable": True,
    }


def test_get_recommendation_by_key_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return 404 when the recommendation does not exist."""

    monkeypatch.setattr(
        recommendations_router,
        "get_recommendation_by_key",
        lambda key: None,
    )

    response = client.get("/recommendations/unknown")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Recommendation not found.",
    }


def test_get_recommendation_categories() -> None:
    """Return all supported recommendation categories."""

    response = client.get("/recommendations/categories")

    assert response.status_code == 200

    assert response.json() == [
        {
            "name": "CASH_FLOW",
            "value": "Cash Flow",
        },
        {
            "name": "BUDGET",
            "value": "Budget",
        },
        {
            "name": "DEBT",
            "value": "Debt",
        },
        {
            "name": "SAVINGS",
            "value": "Savings",
        },
        {
            "name": "GOALS",
            "value": "Goals",
        },
        {
            "name": "HEALTH",
            "value": "Health",
        },
        {
            "name": "BILLS",
            "value": "Bills",
        },
        {
            "name": "WEALTH",
            "value": "Wealth",
        },
        {
            "name": "INCOME",
            "value": "Income",
        },
        {
            "name": "EXPENSES",
            "value": "Expenses",
        },
    ]


def test_get_recommendation_priorities() -> None:
    """Return all supported recommendation priorities."""

    response = client.get("/recommendations/priorities")

    assert response.status_code == 200

    assert response.json() == [
        {
            "name": "LOW",
            "value": 1,
            "score": 100,
        },
        {
            "name": "MEDIUM",
            "value": 2,
            "score": 200,
        },
        {
            "name": "HIGH",
            "value": 3,
            "score": 300,
        },
        {
            "name": "CRITICAL",
            "value": 4,
            "score": 400,
        },
    ]


def test_recommendation_metadata_routes_are_not_treated_as_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep static metadata routes ahead of the dynamic key route."""

    def fail_if_called(key: str) -> Recommendation | None:
        raise AssertionError(f"Dynamic recommendation route received key: {key}")

    monkeypatch.setattr(
        recommendations_router,
        "get_recommendation_by_key",
        fail_if_called,
    )

    categories_response = client.get("/recommendations/categories")
    priorities_response = client.get("/recommendations/priorities")

    assert categories_response.status_code == 200
    assert priorities_response.status_code == 200
