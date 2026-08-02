"""Tests for the AI financial coach API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routers import coach as coach_router
from src.core.exceptions import ExternalServiceError
from src.financial.scenarios.factory import register_default_scenario_handlers
from src.financial.scenarios.service import reset_scenario_handlers

client = TestClient(app)


def setup_function() -> None:
    """Ensure scenario handlers are registered before each test."""
    reset_scenario_handlers()
    register_default_scenario_handlers()


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
