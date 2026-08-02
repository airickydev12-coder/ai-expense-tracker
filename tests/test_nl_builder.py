"""Tests for AI-assisted natural-language scenario parsing."""

from decimal import Decimal

import anthropic
import httpx
import pytest

from src.core.exceptions import ExternalServiceError, ValidationError
from src.financial.debt.models import Debt
from src.financial.scenarios import nl_builder
from src.financial.scenarios.models import ScenarioType

_CATEGORIES = ["Food", "Transportation", "Housing"]


def _debt(debt_id: int = 1, name: str = "Car Loan") -> Debt:
    return Debt(
        id=debt_id,
        name=name,
        balance=Decimal("5000"),
        interest_rate=6.5,
        minimum_payment=Decimal("200"),
    )


def test_parse_scenario_text_maps_to_scenario_run_request_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A valid draft from Claude should map to ScenarioRunRequest fields, stripping null horizon."""

    def fake_request_draft(text: str, categories: list[str], debts: list[Debt]) -> dict:
        return {
            "scenario_type": "Expense Reduction",
            "name": "Cut Dining Out",
            "description": "Reduce food spending by 20 percent.",
            "parameters": {
                "category": "Food",
                "reduction_percentage": 20,
                "horizon_months": None,
            },
        }

    monkeypatch.setattr(nl_builder, "_request_scenario_draft", fake_request_draft)

    result = nl_builder.parse_scenario_text("cut dining out by 20%", _CATEGORIES, [])

    assert result["scenario_type"] == ScenarioType.EXPENSE_REDUCTION
    assert result["name"] == "Cut Dining Out"
    assert result["parameters"] == {"category": "Food", "reduction_percentage": 20}


def test_parse_scenario_text_keeps_present_horizon_months(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request_draft(text: str, categories: list[str], debts: list[Debt]) -> dict:
        return {
            "scenario_type": "Income Increase",
            "name": "Raise",
            "description": "Model a 10 percent raise over 6 months.",
            "parameters": {"increase_percentage": 10, "horizon_months": 6},
        }

    monkeypatch.setattr(nl_builder, "_request_scenario_draft", fake_request_draft)

    result = nl_builder.parse_scenario_text("raise over next 6 months", _CATEGORIES, [])

    assert result["parameters"] == {"increase_percentage": 10, "horizon_months": 6}


def test_parse_scenario_text_filters_irrelevant_parameter_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request_draft(text: str, categories: list[str], debts: list[Debt]) -> dict:
        return {
            "scenario_type": "Additional Savings",
            "name": "Save More",
            "description": "Save an extra $100 per month.",
            "parameters": {
                "additional_monthly_savings": 100,
                "horizon_months": None,
                "category": "Food",
            },
        }

    monkeypatch.setattr(nl_builder, "_request_scenario_draft", fake_request_draft)

    result = nl_builder.parse_scenario_text("save an extra $100 a month", _CATEGORIES, [])

    assert result["parameters"] == {"additional_monthly_savings": 100}


def test_parse_scenario_text_raises_validation_error_for_unknown_debt_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request_draft(text: str, categories: list[str], debts: list[Debt]) -> dict:
        return {
            "scenario_type": "Extra Debt Payment",
            "name": "Extra Car Payment",
            "description": "Pay an extra $200 per month.",
            "parameters": {
                "debt_id": 999,
                "extra_monthly_payment": 200,
                "horizon_months": None,
            },
        }

    monkeypatch.setattr(nl_builder, "_request_scenario_draft", fake_request_draft)

    with pytest.raises(ValidationError):
        nl_builder.parse_scenario_text("pay extra on my car loan", _CATEGORIES, [_debt()])


def test_request_scenario_draft_wraps_anthropic_errors(
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

    monkeypatch.setattr(nl_builder.ai_client, "get_client", lambda: FakeClient())

    with pytest.raises(ExternalServiceError):
        nl_builder._request_scenario_draft("cut dining out by 20%", _CATEGORIES, [])


def test_build_schema_omits_enum_when_no_debts() -> None:
    schema = nl_builder._build_schema(_CATEGORIES, [])
    debt_payment_branch = schema["properties"]["parameters"]["anyOf"][2]

    assert "enum" not in debt_payment_branch["properties"]["debt_id"]


def test_build_schema_includes_enum_when_debts_present() -> None:
    schema = nl_builder._build_schema(_CATEGORIES, [1, 2])
    debt_payment_branch = schema["properties"]["parameters"]["anyOf"][2]

    assert debt_payment_branch["properties"]["debt_id"]["enum"] == [1, 2]
