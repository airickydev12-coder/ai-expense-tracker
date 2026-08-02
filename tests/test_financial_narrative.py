"""Tests for AI-generated financial snapshot narratives."""

from decimal import Decimal

import anthropic
import httpx
import pytest

from src.core.exceptions import ExternalServiceError
from src.financial.coach import narrative


def build_snapshot() -> dict:
    """Create a representative financial snapshot for narrative tests."""
    return {
        "total_income": Decimal("5000.00"),
        "total_expenses": Decimal("3000.00"),
        "net_cash_flow": Decimal("2000.00"),
        "total_account_balance": Decimal("9000.00"),
        "total_goal_progress": Decimal("2500.00"),
        "total_debt": Decimal("1000.00"),
        "net_worth": Decimal("10500.00"),
        "health_score": 82,
        "health_status": "Excellent",
        "budget_report": [
            {
                "category": "Food",
                "limit": Decimal("500.00"),
                "spent": Decimal("300.00"),
                "remaining": Decimal("200.00"),
                "status": "Under Budget",
            }
        ],
        "goals": [
            {
                "id": 1,
                "name": "Emergency Fund",
                "target_amount": Decimal("10000.00"),
                "current_amount": Decimal("2500.00"),
            }
        ],
    }


def test_generate_financial_narrative_returns_request_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A generated narrative should pass through unchanged from the request."""
    captured_prompt: dict[str, str] = {}

    def fake_request_narrative(prompt: str) -> str:
        captured_prompt["value"] = prompt
        return "Your finances look healthy overall."

    monkeypatch.setattr(narrative, "_request_narrative", fake_request_narrative)

    result = narrative.generate_financial_narrative(build_snapshot())

    assert result == "Your finances look healthy overall."
    assert "5,000.00" in captured_prompt["value"]
    assert "Emergency Fund" in captured_prompt["value"]
    assert "Food" in captured_prompt["value"]


def test_generate_financial_narrative_handles_missing_income(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Metrics that can't be calculated should be labeled, not crash the build."""
    snapshot = build_snapshot()
    snapshot["total_income"] = Decimal("0")
    snapshot["total_expenses"] = Decimal("0")

    captured_prompt: dict[str, str] = {}

    def fake_request_narrative(prompt: str) -> str:
        captured_prompt["value"] = prompt
        return "Narrative text."

    monkeypatch.setattr(narrative, "_request_narrative", fake_request_narrative)

    result = narrative.generate_financial_narrative(snapshot)

    assert result == "Narrative text."
    assert "not calculable" in captured_prompt["value"]


def test_generate_financial_narrative_handles_empty_goals_and_budgets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No goals/budgets should produce a graceful summary, not crash."""
    snapshot = build_snapshot()
    snapshot["goals"] = []
    snapshot["budget_report"] = []

    monkeypatch.setattr(narrative, "_request_narrative", lambda prompt: "ok")

    assert narrative.generate_financial_narrative(snapshot) == "ok"


def test_request_narrative_wraps_anthropic_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An Anthropic API failure should be wrapped in ExternalServiceError."""

    class FakeMessages:
        def create(self, **kwargs: object) -> None:
            raise anthropic.APIConnectionError(
                message="Connection error.",
                request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
            )

    class FakeClient:
        messages = FakeMessages()

    monkeypatch.setattr(narrative.ai_client, "get_client", lambda: FakeClient())

    with pytest.raises(ExternalServiceError):
        narrative._request_narrative("prompt")
