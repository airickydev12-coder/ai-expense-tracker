"""Tests for the financial recommendations API."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routers import recommendations as recommendations_router
from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.history import RecommendationRecord
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.recommendations.status import RecommendationStatus

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


def make_test_record() -> RecommendationRecord:
    """Create a lifecycle record used by lifecycle-action API tests."""

    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    return RecommendationRecord(
        recommendation_key="budget:reduce_dining_expenses",
        status=RecommendationStatus.DISMISSED,
        created_at=timestamp,
        updated_at=timestamp,
        note="Already on it",
    )


def test_dismiss_recommendation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dismiss a recommendation and return its updated lifecycle record."""

    captured_arguments: dict[str, object] = {}

    def fake_dismiss(key: str, note: str = "") -> RecommendationRecord:
        captured_arguments["key"] = key
        captured_arguments["note"] = note
        return make_test_record()

    monkeypatch.setattr(
        recommendations_router,
        "dismiss_recommendation",
        fake_dismiss,
    )

    response = client.post(
        "/recommendations/budget:reduce_dining_expenses/dismiss",
        json={"note": "Already on it"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "recommendation_key": "budget:reduce_dining_expenses",
        "status": "DISMISSED",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "note": "Already on it",
    }
    assert captured_arguments == {
        "key": "budget:reduce_dining_expenses",
        "note": "Already on it",
    }


def test_dismiss_recommendation_defaults_to_empty_note(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Allow the request body to be omitted entirely."""

    captured_note: str | None = None

    def fake_dismiss(key: str, note: str = "") -> RecommendationRecord:
        nonlocal captured_note
        captured_note = note
        return make_test_record()

    monkeypatch.setattr(
        recommendations_router,
        "dismiss_recommendation",
        fake_dismiss,
    )

    response = client.post("/recommendations/budget:reduce_dining_expenses/dismiss")

    assert response.status_code == 200
    assert captured_note == ""


def test_dismiss_recommendation_returns_404_when_not_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return 404 when no lifecycle record exists for the key."""

    monkeypatch.setattr(
        recommendations_router,
        "dismiss_recommendation",
        lambda key, note="": None,
    )

    response = client.post("/recommendations/unknown/dismiss")

    assert response.status_code == 404


def test_complete_recommendation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Complete a recommendation and return its updated lifecycle record."""

    record = RecommendationRecord(
        recommendation_key="budget:reduce_dining_expenses",
        status=RecommendationStatus.COMPLETED,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    monkeypatch.setattr(
        recommendations_router,
        "complete_recommendation",
        lambda key, note="": record,
    )

    response = client.post("/recommendations/budget:reduce_dining_expenses/complete")

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"


def test_complete_recommendation_returns_404_when_not_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return 404 when no lifecycle record exists for the key."""

    monkeypatch.setattr(
        recommendations_router,
        "complete_recommendation",
        lambda key, note="": None,
    )

    response = client.post("/recommendations/unknown/complete")

    assert response.status_code == 404


def test_suppress_recommendation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Suppress a recommendation and return its updated lifecycle record."""

    record = RecommendationRecord(
        recommendation_key="budget:reduce_dining_expenses",
        status=RecommendationStatus.SUPPRESSED,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    monkeypatch.setattr(
        recommendations_router,
        "suppress_recommendation",
        lambda key, note="": record,
    )

    response = client.post("/recommendations/budget:reduce_dining_expenses/suppress")

    assert response.status_code == 200
    assert response.json()["status"] == "SUPPRESSED"


def test_suppress_recommendation_returns_404_when_not_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return 404 when no lifecycle record exists for the key."""

    monkeypatch.setattr(
        recommendations_router,
        "suppress_recommendation",
        lambda key, note="": None,
    )

    response = client.post("/recommendations/unknown/suppress")

    assert response.status_code == 404
