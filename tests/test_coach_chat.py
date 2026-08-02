"""Tests for the AI financial coach tool-use chat loop."""

from types import SimpleNamespace

import anthropic
import httpx
import pytest

from src.core.exceptions import ExternalServiceError, ValidationError
from src.financial.coach import chat


def _text_message(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text=text)],
    )


def _tool_use_message(name: str, tool_use_id: str = "toolu_1") -> SimpleNamespace:
    return SimpleNamespace(
        stop_reason="tool_use",
        content=[SimpleNamespace(type="tool_use", name=name, id=tool_use_id, input={})],
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
