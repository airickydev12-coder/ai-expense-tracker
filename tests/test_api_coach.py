"""Tests for the AI financial coach API endpoints."""

from fastapi.testclient import TestClient

from src.api.main import app
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
