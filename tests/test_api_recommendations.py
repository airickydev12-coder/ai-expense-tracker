"""Tests for the financial recommendations API."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routers import recommendations as recommendations_router
from src.financial.recommendations.models import Recommendation


client = TestClient(app)


def test_get_recommendations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return serialized financial recommendations."""

    test_recommendations = [
        Recommendation(
            priority="HIGH",
            category="budget",
            title="Reduce dining expenses",
            message="Dining expenses are above your target.",
            action="Set a weekly dining limit.",
            rationale=("Dining represents a large share of spending."),
            source_rule="DiningSpendingRule",
        ),
    ]

    monkeypatch.setattr(
        recommendations_router,
        "build_recommendations",
        lambda limit=None: test_recommendations,
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
        "rationale": ("Dining represents a large share of spending."),
        "source_rule": "DiningSpendingRule",
        "is_actionable": True,
    }


def test_get_recommendations_passes_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pass the requested recommendation limit to the service."""

    captured_limit: int | None = None

    def fake_build_recommendations(
        limit: int | None = None,
    ) -> list[Recommendation]:
        nonlocal captured_limit

        captured_limit = limit

        return []

    monkeypatch.setattr(
        recommendations_router,
        "build_recommendations",
        fake_build_recommendations,
    )

    response = client.get("/recommendations?limit=3")

    assert response.status_code == 200
    assert response.json() == []
    assert captured_limit == 3


def test_get_recommendations_rejects_invalid_limit() -> None:
    """Reject recommendation limits below one."""

    response = client.get("/recommendations?limit=0")

    assert response.status_code == 422


def test_get_recommendation_by_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return a recommendation matching the requested key."""

    recommendation = Recommendation(
        priority="HIGH",
        category="budget",
        title="Reduce dining expenses",
        message="Dining expenses are above your target.",
        action="Set a weekly dining limit.",
        rationale="Dining represents a large share of spending.",
        source_rule="DiningSpendingRule",
    )

    monkeypatch.setattr(
        recommendations_router,
        "get_recommendation_by_key",
        lambda key: recommendation,
    )

    response = client.get("/recommendations/budget:reduce_dining_expenses")

    assert response.status_code == 200
    assert response.json()["key"] == "budget:reduce_dining_expenses"


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
    assert response.json() == {"detail": "Recommendation not found."}
