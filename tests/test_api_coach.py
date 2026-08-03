"""Tests for the AI financial coach API endpoints."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routers import coach as coach_router
from src.core.exceptions import ExternalServiceError, NotFoundError
from src.financial.coach.notes_service import clear_notes
from src.financial.scenarios.factory import register_default_scenario_handlers
from src.financial.scenarios.service import reset_scenario_handlers

client = TestClient(app)


def setup_function() -> None:
    """Ensure scenario handlers are registered and notes are cleared before each test."""
    reset_scenario_handlers()
    register_default_scenario_handlers()
    clear_notes()


def test_get_financial_narrative(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        coach_router.coach_narrative,
        "generate_financial_narrative",
        lambda snapshot: "Your finances look healthy overall.",
    )

    response = client.get("/coach/narrative")

    assert response.status_code == 200
    assert response.json()["narrative"] == "Your finances look healthy overall."


def test_get_recommendation_explanation_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_explain(recommendation_key: str) -> dict:
        assert recommendation_key == "debt:high_interest_debt"
        return {
            "recommendation_key": recommendation_key,
            "reason": "Card A has the highest APR.",
            "evidence": {
                "type": "debt",
                "debt_name": "Card A",
                "debt_balance": Decimal("4800.00"),
                "interest_rate": 27.4,
                "minimum_payment": Decimal("145.00"),
                "extra_monthly_payment": 250.0,
                "payoff_months_saved": 11,
                "total_interest_saved": Decimal("620.00"),
                "total_debt": Decimal("4800.00"),
            },
            "expected_impact": "Payoff about 11 months sooner.",
            "confidence": "High",
            "assumptions": ["Income remains stable."],
        }

    monkeypatch.setattr(
        coach_router.recommendation_explainer,
        "explain_recommendation",
        fake_explain,
    )

    response = client.get("/coach/recommendations/debt:high_interest_debt/explanation")

    assert response.status_code == 200
    body = response.json()
    assert body["reason"] == "Card A has the highest APR."
    assert body["evidence"]["debt_name"] == "Card A"
    assert body["confidence"] == "High"


def test_get_recommendation_explanation_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_explain(recommendation_key: str) -> dict:
        raise NotFoundError("No recommendation was found.")

    monkeypatch.setattr(
        coach_router.recommendation_explainer,
        "explain_recommendation",
        fake_explain,
    )

    response = client.get("/coach/recommendations/debt:unknown/explanation")

    assert response.status_code == 404


def test_get_recommendation_explanation_non_debt_category_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_explain(recommendation_key: str) -> dict:
        assert recommendation_key == "cash_flow:negative"
        return {
            "recommendation_key": recommendation_key,
            "reason": "Cash flow is negative this period.",
            "evidence": {
                "type": "aggregate",
                "net_cash_flow": Decimal("-125.00"),
                "total_income": Decimal("0.00"),
                "total_debt": Decimal("0.00"),
            },
            "expected_impact": "Reduce spending or increase income.",
            "confidence": "Medium",
            "assumptions": ["No new income sources are added."],
        }

    monkeypatch.setattr(
        coach_router.recommendation_explainer,
        "explain_recommendation",
        fake_explain,
    )

    response = client.get("/coach/recommendations/cash_flow:negative/explanation")

    assert response.status_code == 200
    body = response.json()
    assert body["evidence"]["type"] == "aggregate"
    assert body["evidence"]["net_cash_flow"] == "-125.00"


def test_get_monthly_review_no_history(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        coach_router.coach_monthly_review,
        "generate_monthly_review",
        lambda snapshot: {
            "status": "no_history",
            "message": "No financial snapshot has been recorded yet.",
        },
    )

    response = client.get("/coach/monthly-review")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_history"
    assert body["overall_summary"] is None


def test_get_monthly_review_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_review(snapshot: dict) -> dict:
        return {
            "status": "ok",
            "period_start": "2026-07-01T00:00:00+00:00",
            "period_end": "2026-08-01T00:00:00+00:00",
            "overall_summary": "Overall summary.",
            "income_vs_expenses": {
                "narrative": "Income narrative.",
                "income_change": Decimal("500.00"),
                "expense_change": Decimal("-100.00"),
            },
            "cash_flow": {
                "narrative": "Cash flow narrative.",
                "change": Decimal("600.00"),
                "direction": "Improving",
            },
            "debt_progress": {
                "narrative": "Debt narrative.",
                "total_debt": Decimal("1000.00"),
            },
            "savings_progress": {"narrative": "Savings narrative."},
            "goal_status": {"narrative": "Goals narrative."},
            "health_score": {
                "narrative": "Health score narrative.",
                "change": Decimal("5"),
                "direction": "Improving",
                "current_score": 80,
            },
            "top_actions": [
                {
                    "key": "debt:high_interest_debt",
                    "title": "High Interest Debt",
                    "message": "Card A has a high interest rate.",
                    "action": "Prioritize this debt for repayment.",
                    "priority": "HIGH",
                }
            ],
            "category_trends": [
                {"category": "Food", "change": Decimal("45.50"), "direction": "Increasing"}
            ],
            "known_gaps": [],
        }

    monkeypatch.setattr(
        coach_router.coach_monthly_review,
        "generate_monthly_review",
        fake_review,
    )

    response = client.get("/coach/monthly-review")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["overall_summary"] == "Overall summary."
    assert body["top_actions"][0]["title"] == "High Interest Debt"
    assert body["category_trends"][0]["category"] == "Food"


def test_post_monthly_review_saves_when_status_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ok_review = {
        "status": "ok",
        "period_start": "2026-07-01T00:00:00+00:00",
        "period_end": "2026-08-01T00:00:00+00:00",
        "overall_summary": "Overall summary.",
        "income_vs_expenses": None,
        "cash_flow": None,
        "debt_progress": None,
        "savings_progress": None,
        "goal_status": None,
        "health_score": None,
        "top_actions": None,
        "known_gaps": None,
    }

    monkeypatch.setattr(
        coach_router.coach_monthly_review,
        "generate_monthly_review",
        lambda snapshot: ok_review,
    )

    recorded: dict = {}

    def fake_record_monthly_review(review: dict) -> dict:
        recorded["review"] = review
        return {**review, "generated_at": "2026-08-02T12:00:00+00:00"}

    monkeypatch.setattr(
        coach_router, "record_monthly_review", fake_record_monthly_review
    )

    response = client.post("/coach/monthly-review")

    assert response.status_code == 200
    body = response.json()
    assert body["generated_at"] == "2026-08-02T12:00:00+00:00"
    assert recorded["review"]["status"] == "ok"


def test_post_monthly_review_does_not_save_when_status_not_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    degraded_review = {
        "status": "no_history",
        "message": "No financial snapshot has been recorded yet.",
    }

    monkeypatch.setattr(
        coach_router.coach_monthly_review,
        "generate_monthly_review",
        lambda snapshot: degraded_review,
    )

    def fail_if_called(review: dict) -> dict:
        raise AssertionError("record_monthly_review must not be called for degraded status.")

    monkeypatch.setattr(coach_router, "record_monthly_review", fail_if_called)

    response = client.post("/coach/monthly-review")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_history"
    assert body["generated_at"] is None


def test_get_insights() -> None:
    response = client.get("/coach/insights")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_coaching_session() -> None:
    response = client.get("/coach/session")

    assert response.status_code == 200
    body = response.json()
    assert "summary" in body
    assert "insights" in body
    assert "next_steps" in body


def test_post_chat_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        coach_router.coach_chat, "run_coach_chat", lambda history: "You're doing well."
    )

    response = client.post(
        "/coach/chat",
        json={"messages": [{"role": "user", "content": "How am I doing?"}]},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "You're doing well."


def test_post_chat_endpoint_rejects_non_user_last_message() -> None:
    response = client.post(
        "/coach/chat",
        json={
            "messages": [
                {"role": "user", "content": "How am I doing?"},
                {"role": "assistant", "content": "You're doing well."},
            ]
        },
    )

    assert response.status_code == 400


def test_post_chat_endpoint_rejects_empty_messages() -> None:
    response = client.post("/coach/chat", json={"messages": []})

    assert response.status_code == 422


def test_post_chat_endpoint_propagates_external_service_error_as_502(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run_coach_chat(history: list[dict]) -> str:
        raise ExternalServiceError("Coach chat is unavailable.")

    monkeypatch.setattr(coach_router.coach_chat, "run_coach_chat", fake_run_coach_chat)

    response = client.post(
        "/coach/chat",
        json={"messages": [{"role": "user", "content": "How am I doing?"}]},
    )

    assert response.status_code == 502


def test_list_notes_returns_empty_when_none_saved() -> None:
    response = client.get("/coach/notes")

    assert response.status_code == 200
    assert response.json() == []


def test_create_and_list_notes() -> None:
    create_response = client.post(
        "/coach/notes",
        json={"title": "Rent", "content": "Landlord raises rent every March."},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "Rent"
    assert created["content"] == "Landlord raises rent every March."
    assert "created_at" in created

    list_response = client.get("/coach/notes")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_delete_note_removes_it() -> None:
    created = client.post(
        "/coach/notes",
        json={"title": "Rent", "content": "Landlord raises rent every March."},
    ).json()

    delete_response = client.delete(f"/coach/notes/{created['id']}")

    assert delete_response.status_code == 200
    assert delete_response.json()["title"] == "Rent"
    assert client.get("/coach/notes").json() == []


def test_delete_note_returns_404_for_unknown_id() -> None:
    response = client.delete("/coach/notes/999999")

    assert response.status_code == 404
