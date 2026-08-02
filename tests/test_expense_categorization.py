"""Tests for AI-assisted expense category suggestion."""

import anthropic
import httpx
import pytest

from src.core.exceptions import ExternalServiceError
from src.financial.expenses import categorization
from src.financial.shared.categories import ExpenseCategory


def test_suggest_category_returns_expense_category(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A valid category string from Claude should map to the enum member."""

    def fake_request_category(name: str) -> str:
        assert name == "Trader Joe's"
        return "Food"

    monkeypatch.setattr(categorization, "_request_category", fake_request_category)
    assert categorization.suggest_category("Trader Joe's") == ExpenseCategory.FOOD


def test_request_category_wraps_anthropic_errors(
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

    monkeypatch.setattr(categorization.ai_client, "get_client", lambda: FakeClient())

    with pytest.raises(ExternalServiceError):
        categorization._request_category("Coffee")
