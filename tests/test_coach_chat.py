"""Tests for the AI financial coach tool-use chat loop."""

import contextlib
from decimal import Decimal
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from src.core.db import clear_test_database, initialize_database, set_test_database
from src.core.exceptions import ExternalServiceError, ValidationError
from src.financial.budgets.service import budgets as _budgets
from src.financial.coach import chat
from src.financial.expenses.service import add_expense, expenses as _expenses
from src.financial.goals.service import goals as _goals
from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.history_service import (
    get_recommendation_record,
    register_recommendation,
    reset_recommendation_history,
)
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.scenarios.factory import register_default_scenario_handlers
from src.financial.scenarios.service import reset_scenario_handlers
from src.financial.scenarios.workspace import scenario_workspace
from src.financial.scenarios.workspace_service import (
    save_result_to_workspace as _real_save_result_to_workspace,
)
from src.financial.shared.categories import ExpenseCategory


@contextlib.contextmanager
def _isolated_test_database(tmp_path):
    """Redirect all SQLite writes to a throwaway DB for the duration of a test."""
    test_db_path = tmp_path / "test_stage4_write_tools.db"
    initialize_database(test_db_path)
    set_test_database(test_db_path)
    try:
        yield
    finally:
        clear_test_database()


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


def test_tool_search_saved_content_delegates_to_search_saved_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    def fake_search_saved_content(query, limit) -> dict:
        captured["query"] = query
        captured["limit"] = limit
        return {"monthly_reviews": [], "scenarios": []}

    monkeypatch.setattr(chat, "search_saved_content", fake_search_saved_content)

    result = chat._tool_search_saved_content(query="emergency fund")

    assert captured == {"query": "emergency fund", "limit": 5}
    assert result == {"monthly_reviews": [], "scenarios": []}


def test_run_coach_chat_executes_search_saved_content_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            _tool_use_message(
                "search_saved_content", input={"query": "emergency fund"}
            ),
            _text_message("Last month we discussed your emergency fund."),
        ]
    )

    monkeypatch.setattr(chat, "_request_completion", lambda messages: next(responses))
    monkeypatch.setattr(
        chat,
        "search_saved_content",
        lambda query=None, limit=5: {"monthly_reviews": [], "scenarios": []},
    )

    reply = chat.run_coach_chat(
        [{"role": "user", "content": "What did we decide about my emergency fund?"}]
    )

    assert reply == "Last month we discussed your emergency fund."


# --- dismiss_recommendation: confirmed flag gate ----------------------------


def _build_test_recommendation() -> Recommendation:
    return Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.DEBT,
        title="High Interest Debt",
        message="You have high-interest debt.",
        action="Prioritize repayment.",
    )


def test_tool_dismiss_recommendation_refuses_when_not_confirmed() -> None:
    reset_recommendation_history()
    recommendation = _build_test_recommendation()
    register_recommendation(recommendation)
    try:
        result = chat._tool_dismiss_recommendation(
            recommendation_key=recommendation.key, confirmed=False
        )

        assert result["dismissed"] is False
        record = get_recommendation_record(recommendation.key)
        assert record is not None
        assert record.status.value != "Dismissed"
    finally:
        reset_recommendation_history()


def test_tool_dismiss_recommendation_dismisses_real_recommendation_when_confirmed() -> None:
    reset_recommendation_history()
    recommendation = _build_test_recommendation()
    register_recommendation(recommendation)
    try:
        result = chat._tool_dismiss_recommendation(
            recommendation_key=recommendation.key,
            confirmed=True,
            note="Already addressed.",
        )

        assert result == {
            "dismissed": True,
            "recommendation_key": recommendation.key,
            "status": "Dismissed",
        }
        record = get_recommendation_record(recommendation.key)
        assert record is not None
        assert record.status.value == "Dismissed"
    finally:
        reset_recommendation_history()


def test_tool_dismiss_recommendation_rejects_unregistered_key() -> None:
    reset_recommendation_history()
    try:
        result = chat._tool_dismiss_recommendation(
            recommendation_key="debt:not_real", confirmed=True
        )

        assert result["dismissed"] is False
        assert "list_recommendations" in result["reason"]
    finally:
        reset_recommendation_history()


def test_run_coach_chat_executes_dismiss_recommendation_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            _tool_use_message(
                "dismiss_recommendation",
                input={
                    "recommendation_key": "debt:high_interest_debt",
                    "confirmed": True,
                },
            ),
            _text_message("Done -- I've dismissed that recommendation."),
        ]
    )

    monkeypatch.setattr(chat, "_request_completion", lambda messages: next(responses))

    received: dict = {}

    def fake_dismiss(recommendation_key: str, confirmed: bool = False, note: str = "") -> dict:
        received["recommendation_key"] = recommendation_key
        received["confirmed"] = confirmed
        return {
            "dismissed": True,
            "recommendation_key": recommendation_key,
            "status": "Dismissed",
        }

    monkeypatch.setitem(chat._TOOL_FUNCTIONS, "dismiss_recommendation", fake_dismiss)

    reply = chat.run_coach_chat(
        [{"role": "user", "content": "Yes, dismiss that recommendation."}]
    )

    assert reply == "Done -- I've dismissed that recommendation."
    assert received == {"recommendation_key": "debt:high_interest_debt", "confirmed": True}


# --- save_scenario: confirmed flag gate -------------------------------------


def test_tool_save_scenario_refuses_when_not_confirmed() -> None:
    scenario_workspace.clear()
    try:
        result = chat._tool_save_scenario(
            scenario_type="Additional Savings",
            name="Save More Each Month",
            confirmed=False,
            additional_monthly_savings=300.0,
        )

        assert result["saved"] is False
        assert scenario_workspace.is_empty()
    finally:
        scenario_workspace.clear()


def test_tool_save_scenario_saves_real_scenario_when_confirmed(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Prove confirmed=True re-runs the scenario for real and persists it."""
    reset_scenario_handlers()
    register_default_scenario_handlers()
    scenario_workspace.clear()

    file_path = tmp_path / "scenario_workspace.json"
    monkeypatch.setattr(
        chat,
        "save_result_to_workspace",
        lambda result: _real_save_result_to_workspace(result, file_path),
    )

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

    try:
        result = chat._tool_save_scenario(
            scenario_type="Additional Savings",
            name="Save More Each Month",
            confirmed=True,
            additional_monthly_savings=300.0,
        )

        assert result["saved"] is True
        assert result["name"]
        assert len(scenario_workspace.get_results()) == 1
    finally:
        scenario_workspace.clear()


def test_run_coach_chat_executes_save_scenario_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            _tool_use_message(
                "save_scenario",
                input={
                    "scenario_type": "Additional Savings",
                    "name": "Save More Each Month",
                    "confirmed": True,
                    "additional_monthly_savings": 300.0,
                },
            ),
            _text_message("Saved that scenario for you."),
        ]
    )

    monkeypatch.setattr(chat, "_request_completion", lambda messages: next(responses))

    received: dict = {}

    def fake_save_scenario(
        scenario_type: str, name: str, confirmed: bool = False, **kwargs: object
    ) -> dict:
        received["scenario_type"] = scenario_type
        received["confirmed"] = confirmed
        return {"saved": True, "name": name, "description": ""}

    monkeypatch.setitem(chat._TOOL_FUNCTIONS, "save_scenario", fake_save_scenario)

    reply = chat.run_coach_chat(
        [{"role": "user", "content": "Yes, save that scenario."}]
    )

    assert reply == "Saved that scenario for you."
    assert received == {"scenario_type": "Additional Savings", "confirmed": True}


# --- add_goal: confirmed flag gate ------------------------------------------


def test_tool_add_goal_refuses_when_not_confirmed(tmp_path) -> None:
    _goals.clear()
    with _isolated_test_database(tmp_path):
        result = chat._tool_add_goal(
            name="Vacation Fund", target_amount=2000.0, confirmed=False
        )

        assert result["added"] is False
        assert _goals == []


def test_tool_add_goal_creates_real_goal_when_confirmed(tmp_path) -> None:
    _goals.clear()
    try:
        with _isolated_test_database(tmp_path):
            result = chat._tool_add_goal(
                name="Vacation Fund",
                target_amount=2000.0,
                confirmed=True,
                current_amount=250.0,
            )

            assert result["added"] is True
            assert result["goal"]["name"] == "Vacation Fund"
            assert len(_goals) == 1
            assert _goals[0].name == "Vacation Fund"
    finally:
        _goals.clear()


def test_run_coach_chat_executes_add_goal_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter(
        [
            _tool_use_message(
                "add_goal",
                input={
                    "name": "Vacation Fund",
                    "target_amount": 2000.0,
                    "confirmed": True,
                },
            ),
            _text_message("Added your Vacation Fund goal."),
        ]
    )

    monkeypatch.setattr(chat, "_request_completion", lambda messages: next(responses))

    received: dict = {}

    def fake_add_goal(name: str, target_amount: float, confirmed: bool = False, **kwargs: object) -> dict:
        received["name"] = name
        received["target_amount"] = target_amount
        received["confirmed"] = confirmed
        return {"added": True, "goal": {"id": 1, "name": name}}

    monkeypatch.setitem(chat._TOOL_FUNCTIONS, "add_goal", fake_add_goal)

    reply = chat.run_coach_chat(
        [{"role": "user", "content": "Yes, add that goal."}]
    )

    assert reply == "Added your Vacation Fund goal."
    assert received == {"name": "Vacation Fund", "target_amount": 2000.0, "confirmed": True}


# --- update_budget: confirmed flag gate -------------------------------------


def test_tool_update_budget_refuses_when_not_confirmed(tmp_path) -> None:
    _budgets.clear()
    with _isolated_test_database(tmp_path):
        result = chat._tool_update_budget(
            category="Food", limit=400.0, confirmed=False
        )

        assert result["updated"] is False
        assert _budgets == []


def test_tool_update_budget_updates_real_budget_when_confirmed(tmp_path) -> None:
    _budgets.clear()
    try:
        with _isolated_test_database(tmp_path):
            result = chat._tool_update_budget(
                category="Food", limit=400.0, confirmed=True
            )

            assert result["updated"] is True
            assert result["budget"]["category"] == "Food"
            assert result["budget"]["limit"] == "400.00"
            assert len(_budgets) == 1
            assert _budgets[0].category == ExpenseCategory.FOOD
    finally:
        _budgets.clear()


def test_run_coach_chat_executes_update_budget_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter(
        [
            _tool_use_message(
                "update_budget",
                input={"category": "Food", "limit": 400.0, "confirmed": True},
            ),
            _text_message("Set your Food budget to $400."),
        ]
    )

    monkeypatch.setattr(chat, "_request_completion", lambda messages: next(responses))

    received: dict = {}

    def fake_update_budget(category: str, limit: float, confirmed: bool = False) -> dict:
        received["category"] = category
        received["limit"] = limit
        received["confirmed"] = confirmed
        return {"updated": True, "budget": {"category": category, "limit": str(limit)}}

    monkeypatch.setitem(chat._TOOL_FUNCTIONS, "update_budget", fake_update_budget)

    reply = chat.run_coach_chat(
        [{"role": "user", "content": "Yes, set that budget."}]
    )

    assert reply == "Set your Food budget to $400."
    assert received == {"category": "Food", "limit": 400.0, "confirmed": True}


# --- categorize_expense: confirmed flag gate --------------------------------


def test_tool_categorize_expense_refuses_when_not_confirmed(tmp_path) -> None:
    _expenses.clear()
    try:
        with _isolated_test_database(tmp_path):
            expense = add_expense(
                name="Coffee", category=ExpenseCategory.OTHER, amount=Decimal("5.00")
            )

            result = chat._tool_categorize_expense(
                expense_id=expense.id, category="Food", confirmed=False
            )

            assert result["categorized"] is False
            assert _expenses[0].category == ExpenseCategory.OTHER
    finally:
        _expenses.clear()


def test_tool_categorize_expense_recategorizes_real_expense_when_confirmed(
    tmp_path,
) -> None:
    _expenses.clear()
    try:
        with _isolated_test_database(tmp_path):
            expense = add_expense(
                name="Coffee", category=ExpenseCategory.OTHER, amount=Decimal("5.00")
            )

            result = chat._tool_categorize_expense(
                expense_id=expense.id, category="Food", confirmed=True
            )

            assert result["categorized"] is True
            assert result["expense"]["category"] == "Food"
            assert _expenses[0].category == ExpenseCategory.FOOD
    finally:
        _expenses.clear()


def test_tool_categorize_expense_rejects_unknown_expense_id(tmp_path) -> None:
    _expenses.clear()
    try:
        with _isolated_test_database(tmp_path):
            result = chat._tool_categorize_expense(
                expense_id=999999, category="Food", confirmed=True
            )

            assert result["categorized"] is False
            assert "get_expense_details" in result["reason"]
    finally:
        _expenses.clear()


def test_run_coach_chat_executes_categorize_expense_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            _tool_use_message(
                "categorize_expense",
                input={"expense_id": 7, "category": "Food", "confirmed": True},
            ),
            _text_message("Moved that expense to Food."),
        ]
    )

    monkeypatch.setattr(chat, "_request_completion", lambda messages: next(responses))

    received: dict = {}

    def fake_categorize_expense(
        expense_id: int, category: str, confirmed: bool = False
    ) -> dict:
        received["expense_id"] = expense_id
        received["category"] = category
        received["confirmed"] = confirmed
        return {"categorized": True, "expense": {"id": expense_id, "category": category}}

    monkeypatch.setitem(chat._TOOL_FUNCTIONS, "categorize_expense", fake_categorize_expense)

    reply = chat.run_coach_chat(
        [{"role": "user", "content": "Yes, recategorize it."}]
    )

    assert reply == "Moved that expense to Food."
    assert received == {"expense_id": 7, "category": "Food", "confirmed": True}
