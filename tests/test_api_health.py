"""Tests for the FastAPI health endpoint."""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_check_returns_service_status() -> None:
    """The health endpoint should report a healthy API."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "AI Expense Tracker API",
        "version": "1.0.0",
    }
