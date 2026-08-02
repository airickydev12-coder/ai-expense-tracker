"""Tests for the AI financial coach tool-use chat loop."""

from decimal import Decimal
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from src.core.exceptions import ExternalServiceError, ValidationError
from src.financial.coach import chat
from src.financial.scenarios.factory import register_default_scenario_handlers
from src.financial.scenarios.service import reset_scenario_handlers


def _text_message(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text=text)],
    )


def _tool_use_message(
    name: str,
    tool_use_id: str = "toolu_1",
    input: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        stop_reason="tool_use",
        content=[
            SimpleNamespace(
                type="tool_use",
                name=name,
                id=tool_use_id,
                input=input if input is not None else {},
            )
        ],
    )


def test_run_coach_chat_returns_text_with_no_tool_use(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        chat, "_request_completion", lambda messages: _text_message("You're doing well.")
    )

    reply = chat.run_coach_chat([{"role": "user", "content": "How am I doing?"}])

    assert reply == "You're doing well."


def test_run_coach_chat_executes_tool_and_returns_final_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[dict]] = []
    responses = iter(
        [_tool_use_message("get_financial_snapshot"), _text_message("You have $500 saved.")]
    )

    def fake_request_completion(messages: list[dict]) -> SimpleNamespace:
        calls.append(messages)
        return next(responses)

    monkeypatch.setattr(chat, "_request_completion", fake_request_completion)

    stub_called = False

    def fake_snapshot_tool() -> dict:
        nonlocal stub_called
        stub_called = True
        return {"net_worth": "500"}

    monkeypatch.setitem(chat._TOOL_FUNCTIONS, "get_financial_snapshot", fake_snapshot_tool)

    reply = chat.run_coach_chat([{"role": "user", "content": "What's my net worth?"}])

    assert reply == "You have $500 saved."
    assert stub_called is True
    assert len(calls) == 2
    second_call_messages = calls[1]
    tool_result_message = second_call_messages[-1]
    assert tool_result_message["role"] == "user"
    tool_result_block = tool_result_message["content"][0]
    assert tool_result_block["tool_use_id"] == "toolu_1"
    assert tool_result_block["is_error"] is False


def test_run_coach_chat_wraps_tool_error_as_tool_result_is_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter([_tool_use_message("get_budget_status"), _text_message("Something's off.")])

    def fake_request_completion(messages: list[dict]) -> SimpleNamespace:
        return next(responses)

    monkeypatch.setattr(chat, "_request_completion", fake_request_completion)

    def failing_tool() -> dict:
        raise ValidationError("Budget data is unavailable.")

    monkeypatch.setitem(chat._TOOL_FUNCTIONS, "get_budget_status", failing_tool)

    reply = chat.run_coach_chat([{"role": "user", "content": "Am I on budget?"}])

    assert reply == "Something's off."


def test_run_coach_chat_raises_when_iteration_cap_exceeded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_count = 0

    def fake_request_completion(messages: list[dict]) -> SimpleNamespace:
        nonlocal call_count
        call_count += 1
        return _tool_use_message("get_financial_snapshot")

    monkeypatch.setattr(chat, "_request_completion", fake_request_completion)

    with pytest.raises(ExternalServiceError):
        chat.run_coach_chat([{"role": "user", "content": "Tell me everything."}])

    assert call_count == chat.MAX_TOOL_USE_ITERATIONS


def test_request_completion_wraps_anthropic_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """An Anthropic API failure should be wrapped in ExternalServiceError."""

    class FakeMessages:
        def create(self, **kwargs: object) -> None:
            raise anthropic.APIConnectionError(
                message="Connection error.",
                request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
            )

    class FakeClient:
        messages = FakeMessages()

    monkeypatch.setattr(chat.ai_client, "get_client", lambda: FakeClient())

    with pytest.raises(ExternalServiceError):
        chat._request_completion([{"role": "user", "content": "Hi"}])


def test_execute_tool_returns_error_content_for_unknown_tool_name() -> None:
    content, is_error = chat._execute_tool("not_a_real_tool", {})

    assert is_error is True
    assert "not_a_real_tool" in content


def test_execute_tool_passes_tool_input_as_kwargs() -> None:
    """The dispatcher must thread tool_input through to the tool function."""
    received: dict = {}

    def fake_tool(recommendation_key: str) -> dict:
        received["recommendation_key"] = recommendation_key
        return {"ok": True}

    chat._TOOL_FUNCTIONS["_fake_tool_for_test"] = fake_tool
    try:
        content, is_error = chat._execute_tool(
            "_fake_tool_for_test", {"recommendation_key": "debt:high_interest_debt"}
        )
    finally:
        del chat._TOOL_FUNCTIONS["_fake_tool_for_test"]

    assert is_error is False
    assert received["recommendation_key"] == "debt:high_interest_debt"
    assert "true" in content.lower()


def test_run_coach_chat_executes_parameterized_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A parameterized tool call's input should reach the tool function."""
    responses = iter(
        [
            _tool_use_message(
                "list_recommendations", input={"category": "Debt", "limit": 3}
            ),
            _text_message("Here's what to prioritize."),
        ]
    )

    monkeypatch.setattr(chat, "_request_completion", lambda messages: next(responses))

    received: dict = {}

    def fake_list_recommendations(category=None, priority=None, limit=None) -> dict:
        received["category"] = category
        received["priority"] = priority
        received["limit"] = limit
        return {"recommendations": []}

    monkeypatch.setitem(
        chat._TOOL_FUNCTIONS, "list_recommendations", fake_list_recommendations
    )

    reply = chat.run_coach_chat([{"role": "user", "content": "What should I prioritize?"}])

    assert reply == "Here's what to prioritize."
    assert received == {"category": "Debt", "priority": None, "limit": 3}


def test_run_coach_chat_surfaces_missing_scenario_parameter_as_tool_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A handler ValidationError (e.g. a missing required parameter) shouldn't crash the loop."""
    responses = iter(
        [
            _tool_use_message(
                "run_scenario",
                input={"scenario_type": "Expense Reduction", "name": "Cut Food"},
            ),
            _text_message("I need a reduction percentage to run that."),
        ]
    )

    monkeypatch.setattr(chat, "_request_completion", lambda messages: next(responses))

    reply = chat.run_coach_chat([{"role": "user", "content": "What if I cut food spending?"}])

    assert reply == "I need a reduction percentage to run that."


def test_tool_run_scenario_filters_parameters_by_scenario_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only the parameters relevant to the chosen scenario type should be passed through."""
    captured: dict = {}

    def fake_run_financial_scenario(request, snapshot) -> SimpleNamespace:
        captured["request"] = request
        return SimpleNamespace(to_dict=lambda: {"ok": True})

    monkeypatch.setattr(chat, "build_current_financial_snapshot", lambda: {"total_income": 0})
    monkeypatch.setattr(chat, "run_financial_scenario", fake_run_financial_scenario)

    chat._tool_run_scenario(
        scenario_type="Extra Debt Payment",
        name="Pay Off Card A",
        debt_id=1,
        extra_monthly_payment=200.0,
        reduction_percentage=50.0,  # irrelevant to this scenario type -- must be dropped
    )

    request = captured["request"]
    assert request.parameters == {"debt_id": 1, "extra_monthly_payment": 200.0}


def test_tool_list_recommendations_defaults_limit_to_five(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    def fake_build_recommendations(priority=None, category=None, limit=None) -> list:
        captured["limit"] = limit
        return []

    monkeypatch.setattr(chat, "build_recommendations", fake_build_recommendations)

    result = chat._tool_list_recommendations()

    assert captured["limit"] == 5
    assert result == {"recommendations": []}


def test_tool_recommendation_evidence_delegates_to_get_recommendation_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    def fake_get_recommendation_evidence(recommendation_key: str) -> dict:
        captured["recommendation_key"] = recommendation_key
        return {"recommendation": {}, "evidence": {}}

    monkeypatch.setattr(
        chat, "get_recommendation_evidence", fake_get_recommendation_evidence
    )

    result = chat._tool_recommendation_evidence("debt:high_interest_debt")

    assert captured["recommendation_key"] == "debt:high_interest_debt"
    assert result == {"recommendation": {}, "evidence": {}}


def test_tool_run_scenario_executes_real_scenario_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove the schema-to-parameters mapping works against the real handler chain."""
    reset_scenario_handlers()
    register_default_scenario_handlers()

    snapshot = {
        "total_income": Decimal("5000.00"),
        "total_expenses": Decimal("3000.00"),
        "net_cash_flow": Decimal("2000.00"),
        "total_account_balance": Decimal("9000.00"),
        "total_goal_progress": Decimal("2500.00"),
        "total_debt": Decimal("0"),
        "net_worth": Decimal("11500.00"),
        "health_score": 85,
        "health_status": "Excellent",
    }

    monkeypatch.setattr(chat, "build_current_financial_snapshot", lambda: snapshot)

    result = chat._tool_run_scenario(
        scenario_type="Additional Savings",
        name="Save More Each Month",
        additional_monthly_savings=300.0,
    )

    assert result["scenario_type"] == "ADDITIONAL_SAVINGS"
    # Handlers always derive ScenarioResult.name from their own template,
    # ignoring the caller-supplied name -- pre-existing behavior, not new.
    assert result["name"]
    assert isinstance(result["impacts"], list)
    assert len(result["impacts"]) > 0
