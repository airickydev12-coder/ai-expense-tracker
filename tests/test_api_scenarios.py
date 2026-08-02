"""Tests for the financial scenario API endpoints."""

from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.debt.service import debts
from src.financial.expenses.service import expenses
from src.financial.scenarios.factory import register_default_scenario_handlers
from src.financial.scenarios.service import reset_scenario_handlers
from src.financial.scenarios.workspace import scenario_workspace

client = TestClient(app)


def setup_function() -> None:
    """Reset scenario state and unrelated domain state before each test."""
    reset_scenario_handlers()
    register_default_scenario_handlers()
    scenario_workspace.clear()
    expenses.clear()
    debts.clear()


def test_run_additional_savings_scenario() -> None:
    response = client.post(
        "/scenarios/run",
        json={
            "scenario_type": "Additional Savings",
            "name": "Save More",
            "description": "Save an extra $200 per month.",
            "parameters": {"additional_monthly_savings": 200},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_type"] == "ADDITIONAL_SAVINGS"
    assert body["name"]


def test_run_scenario_missing_required_parameter_returns_400() -> None:
    response = client.post(
        "/scenarios/run",
        json={
            "scenario_type": "Additional Savings",
            "name": "Save More",
            "description": "",
            "parameters": {},
        },
    )

    assert response.status_code == 400


def test_optimize_scenarios() -> None:
    response = client.post("/scenarios/optimize", json={})

    assert response.status_code == 200
    body = response.json()
    assert "candidate_count" in body
    assert "success_count" in body


def test_run_combined_plan() -> None:
    response = client.post(
        "/scenarios/combined",
        json={
            "name": "Combined Plan",
            "description": "Save more and increase income.",
            "requests": [
                {
                    "scenario_type": "Additional Savings",
                    "name": "Save More",
                    "description": "",
                    "parameters": {"additional_monthly_savings": 200},
                },
                {
                    "scenario_type": "Income Increase",
                    "name": "Raise",
                    "description": "",
                    "parameters": {"increase_percentage": 10},
                },
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Combined Plan"


def test_workspace_lifecycle() -> None:
    assert client.get("/scenarios/workspace").json() == []

    saved = client.post(
        "/scenarios/workspace",
        json={
            "scenario_type": "Additional Savings",
            "name": "Save More",
            "description": "",
            "parameters": {"additional_monthly_savings": 200},
        },
    )
    assert saved.status_code == 201
    saved_name = saved.json()["name"]

    listed = client.get("/scenarios/workspace").json()
    assert len(listed) == 1
    assert listed[0]["name"] == saved_name

    deleted = client.delete(f"/scenarios/workspace/{saved_name}")
    assert deleted.status_code == 200
    assert client.get("/scenarios/workspace").json() == []


def test_delete_missing_workspace_result_returns_404() -> None:
    response = client.delete("/scenarios/workspace/Nonexistent")

    assert response.status_code == 404


def test_clear_workspace() -> None:
    client.post(
        "/scenarios/workspace",
        json={
            "scenario_type": "Additional Savings",
            "name": "Save More",
            "description": "",
            "parameters": {"additional_monthly_savings": 200},
        },
    )

    response = client.delete("/scenarios/workspace")

    assert response.status_code == 204
    assert client.get("/scenarios/workspace").json() == []
