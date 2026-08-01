"""Tests for the Financial Goal Planner CLI controller."""

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import cast

import pytest

from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
    GoalPlanningResult,
)
from src.financial.goals.allocation import GoalPriority
from src.financial.goals.models import Goal
from src.presentation import goal_planning_cli

InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


def make_input(
    responses: list[str],
) -> InputFunction:
    """Create an input function that returns supplied responses in order."""
    iterator = iter(responses)

    def fake_input(
        prompt: str,
    ) -> str:
        del prompt
        return next(iterator)

    return fake_input


def collect_output() -> tuple[list[str], OutputFunction]:
    """Create an output collector and its output function."""
    messages: list[str] = []

    def fake_output(
        message: str,
    ) -> None:
        messages.append(message)

    return messages, fake_output


def build_goal(
    *,
    goal_id: int = 1,
    name: str = "Emergency Fund",
    target_amount: Decimal = Decimal("10000.00"),
    current_amount: Decimal = Decimal("4000.00"),
) -> Goal:
    """Create a representative financial goal."""
    return Goal(
        id=goal_id,
        name=name,
        target_amount=target_amount,
        current_amount=current_amount,
    )


def build_goals() -> list[Goal]:
    """Create representative goals for CLI tests."""
    return [
        build_goal(
            goal_id=1,
            name="Emergency Fund",
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("4000.00"),
        ),
        build_goal(
            goal_id=2,
            name="Vacation",
            target_amount=Decimal("3000.00"),
            current_amount=Decimal("600.00"),
        ),
        build_goal(
            goal_id=3,
            name="Car Fund",
            target_amount=Decimal("12000.00"),
            current_amount=Decimal("4800.00"),
        ),
    ]


def build_request(
    goal: Goal,
    *,
    target_date: date = date(2027, 12, 31),
    monthly_contribution: Decimal = Decimal("500.00"),
    priority: GoalPriority = GoalPriority.HIGH,
) -> GoalPlanningRequest:
    """Create a representative goal-planning request."""
    return GoalPlanningRequest(
        goal=goal,
        target_date=target_date,
        planned_monthly_contribution=monthly_contribution,
        priority=priority,
    )


def test_display_goal_planning_menu() -> None:
    messages, output_fn = collect_output()

    goal_planning_cli.display_goal_planning_menu(
        output_fn=output_fn,
    )

    assert messages == [
        "=" * 30,
        "Financial Goal Planner",
        "=" * 30,
        "1. Analyze All Goals",
        "2. Analyze One Goal",
        "3. Monthly Allocation Planner",
        "4. View Planning Requests",
        "5. Update Planning Request",
        "6. Delete Planning Request",
        "7. Return to Main Menu",
    ]


def test_run_goal_planning_menu_returns_to_main_menu() -> None:
    messages, output_fn = collect_output()

    result = goal_planning_cli.run_goal_planning_menu(
        build_goals(),
        input_fn=make_input(["7"]),
        output_fn=output_fn,
        today=date(2027, 1, 1),
    )

    assert result is None
    assert messages[-1] == "Returning to the main menu."


def test_run_goal_planning_menu_routes_to_analyze_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    choices = iter([1, 7])

    def fake_prompt_for_menu_choice(
        prompt: str,
        *,
        minimum: int,
        maximum: int,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> int:
        del prompt
        del minimum
        del maximum
        del input_fn
        del output_fn
        return next(choices)

    def fake_analyze_all_goals_workflow(
        goals: list[Goal],
        *,
        requests_by_goal_id: dict[int, GoalPlanningRequest],
        today: date,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> None:
        del goals
        del requests_by_goal_id
        del today
        del input_fn
        del output_fn
        calls.append("analyze_all")

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        fake_prompt_for_menu_choice,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "analyze_all_goals_workflow",
        fake_analyze_all_goals_workflow,
    )

    goal_planning_cli.run_goal_planning_menu(
        build_goals(),
        output_fn=lambda message: None,
        today=date(2027, 1, 1),
    )

    assert calls == ["analyze_all"]


def test_run_goal_planning_menu_routes_to_analyze_single(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    choices = iter([2, 7])

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: next(choices),
    )

    def fake_workflow(
        goals: list[Goal],
        *,
        requests_by_goal_id: dict[int, GoalPlanningRequest],
        today: date,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> None:
        del goals
        del requests_by_goal_id
        del today
        del input_fn
        del output_fn
        calls.append("analyze_single")

    monkeypatch.setattr(
        goal_planning_cli,
        "analyze_single_goal_workflow",
        fake_workflow,
    )

    goal_planning_cli.run_goal_planning_menu(
        build_goals(),
        output_fn=lambda message: None,
        today=date(2027, 1, 1),
    )

    assert calls == ["analyze_single"]


def test_run_goal_planning_menu_routes_to_monthly_allocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    choices = iter([3, 7])

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: next(choices),
    )

    def fake_workflow(
        goals: list[Goal],
        *,
        requests_by_goal_id: dict[int, GoalPlanningRequest],
        today: date,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> None:
        del goals
        del requests_by_goal_id
        del today
        del input_fn
        del output_fn
        calls.append("monthly_allocation")

    monkeypatch.setattr(
        goal_planning_cli,
        "monthly_allocation_workflow",
        fake_workflow,
    )

    goal_planning_cli.run_goal_planning_menu(
        build_goals(),
        output_fn=lambda message: None,
        today=date(2027, 1, 1),
    )

    assert calls == ["monthly_allocation"]


def test_run_goal_planning_menu_routes_to_view_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    choices = iter([4, 7])

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: next(choices),
    )

    def fake_workflow(
        requests_by_goal_id: dict[int, GoalPlanningRequest],
        *,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> None:
        del requests_by_goal_id
        del input_fn
        del output_fn
        calls.append("view_requests")

    monkeypatch.setattr(
        goal_planning_cli,
        "view_planning_requests_workflow",
        fake_workflow,
    )

    goal_planning_cli.run_goal_planning_menu(
        build_goals(),
        output_fn=lambda message: None,
        today=date(2027, 1, 1),
    )

    assert calls == ["view_requests"]


def test_run_goal_planning_menu_reuses_session_request_storage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_store_ids: list[int] = []
    choices = iter([1, 4, 7])

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: next(choices),
    )

    def fake_analyze_workflow(
        goals: list[Goal],
        *,
        requests_by_goal_id: dict[int, GoalPlanningRequest],
        today: date,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> None:
        del goals
        del today
        del input_fn
        del output_fn
        request_store_ids.append(id(requests_by_goal_id))

    def fake_view_workflow(
        requests_by_goal_id: dict[int, GoalPlanningRequest],
        *,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> None:
        del input_fn
        del output_fn
        request_store_ids.append(id(requests_by_goal_id))

    monkeypatch.setattr(
        goal_planning_cli,
        "analyze_all_goals_workflow",
        fake_analyze_workflow,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "view_planning_requests_workflow",
        fake_view_workflow,
    )

    goal_planning_cli.run_goal_planning_menu(
        build_goals(),
        output_fn=lambda message: None,
        today=date(2027, 1, 1),
    )

    assert len(request_store_ids) == 2
    assert request_store_ids[0] == request_store_ids[1]


def test_build_goal_planning_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goal = build_goal()
    messages, output_fn = collect_output()

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_date",
        lambda *args, **kwargs: date(2028, 6, 30),
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_currency",
        lambda *args, **kwargs: Decimal("750.00"),
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_priority",
        lambda *args, **kwargs: GoalPriority.CRITICAL,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_request",
        lambda request: f"Request: {request.goal.name}",
    )

    result = goal_planning_cli.build_goal_planning_request(
        goal,
        today=date(2027, 1, 1),
        input_fn=make_input([]),
        output_fn=output_fn,
    )

    assert result.goal is goal
    assert result.target_date == date(2028, 6, 30)
    assert result.planned_monthly_contribution == Decimal("750.00")
    assert result.priority == GoalPriority.CRITICAL
    assert "Target amount: $10,000.00" in messages
    assert "Current amount: $4,000.00" in messages
    assert "Request: Emergency Fund" in messages


def test_build_goal_planning_request_passes_today_as_minimum_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    planning_date = date(2027, 4, 15)

    def fake_prompt_for_date(
        prompt: str,
        *,
        minimum: date,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> date:
        del prompt
        del input_fn
        del output_fn
        captured["minimum"] = minimum
        return date(2027, 12, 31)

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_date",
        fake_prompt_for_date,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_currency",
        lambda *args, **kwargs: Decimal("500.00"),
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_priority",
        lambda *args, **kwargs: GoalPriority.HIGH,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_request",
        lambda request: "Rendered request",
    )

    goal_planning_cli.build_goal_planning_request(
        build_goal(),
        today=planning_date,
        output_fn=lambda message: None,
    )

    assert captured["minimum"] == planning_date


def test_build_goal_planning_request_rejects_invalid_goal() -> None:
    with pytest.raises(
        TypeError,
        match="goal must be a Goal instance",
    ):
        goal_planning_cli.build_goal_planning_request(
            cast(Goal, object()),
            today=date(2027, 1, 1),
        )


def test_build_goal_planning_request_rejects_invalid_today() -> None:
    with pytest.raises(
        TypeError,
        match="today must be a date instance",
    ):
        goal_planning_cli.build_goal_planning_request(
            build_goal(),
            today=cast(date, "2027-01-01"),
        )


def test_collect_monthly_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    messages, output_fn = collect_output()

    def fake_prompt_for_currency(
        prompt: str,
        *,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> Decimal:
        del input_fn
        del output_fn
        captured["prompt"] = prompt
        return Decimal("1200.00")

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_currency",
        fake_prompt_for_currency,
    )

    result = goal_planning_cli.collect_monthly_budget(
        input_fn=make_input([]),
        output_fn=output_fn,
    )

    assert result == Decimal("1200.00")
    assert captured["prompt"] == "Enter total monthly funding available: $"
    assert messages == [""]


def test_collect_missing_planning_requests_reuses_existing_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goals = build_goals()
    existing_request = build_request(goals[0])
    request_store = {
        goals[0].id: existing_request,
    }
    created_goal_names: list[str] = []

    def fake_build_request(
        goal: Goal,
        *,
        today: date,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> GoalPlanningRequest:
        del today
        del input_fn
        del output_fn
        created_goal_names.append(goal.name)
        return build_request(goal)

    monkeypatch.setattr(
        goal_planning_cli,
        "build_goal_planning_request",
        fake_build_request,
    )

    requests = goal_planning_cli.collect_missing_planning_requests(
        goals,
        requests_by_goal_id=request_store,
        today=date(2027, 1, 1),
        output_fn=lambda message: None,
    )

    assert requests[0] is existing_request
    assert created_goal_names == [
        "Vacation",
        "Car Fund",
    ]
    assert len(request_store) == 3


def test_collect_missing_planning_requests_preserves_goal_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goals = build_goals()

    monkeypatch.setattr(
        goal_planning_cli,
        "build_goal_planning_request",
        lambda goal, **kwargs: build_request(goal),
    )

    requests = goal_planning_cli.collect_missing_planning_requests(
        goals,
        requests_by_goal_id={},
        today=date(2027, 1, 1),
        output_fn=lambda message: None,
    )

    assert [request.goal.id for request in requests] == [
        1,
        2,
        3,
    ]


def test_analyze_planning_requests_delegates_to_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goal = build_goal()
    request = build_request(goal)
    expected_result = cast(
        GoalPlanningResult,
        object(),
    )
    captured: dict[str, object] = {}

    def fake_analyze_goals(
        requests: list[GoalPlanningRequest],
        *,
        total_available: Decimal,
        as_of_date: date | None = None,
    ) -> GoalPlanningResult:
        captured["requests"] = requests
        captured["total_available"] = total_available
        captured["as_of_date"] = as_of_date
        return expected_result

    monkeypatch.setattr(
        goal_planning_cli,
        "analyze_goals",
        fake_analyze_goals,
    )

    result = goal_planning_cli.analyze_planning_requests(
        (request,),
        total_available=Decimal("900.00"),
        as_of_date=date(2027, 1, 1),
    )

    assert result is expected_result
    assert captured["requests"] == [request]
    assert isinstance(captured["requests"], list)
    assert captured["total_available"] == Decimal("900.00")
    assert captured["as_of_date"] == date(2027, 1, 1)


def test_analyze_planning_requests_rejects_empty_requests() -> None:
    with pytest.raises(
        ValueError,
        match="At least one planning request",
    ):
        goal_planning_cli.analyze_planning_requests(
            [],
            total_available=Decimal("500.00"),
        )


def test_analyze_planning_requests_rejects_negative_funding() -> None:
    request = build_request(build_goal())

    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        goal_planning_cli.analyze_planning_requests(
            [request],
            total_available=Decimal("-1.00"),
        )


def test_view_planning_requests_workflow_empty_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages, output_fn = collect_output()
    pause_calls: list[bool] = []

    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: pause_calls.append(True),
    )

    result = goal_planning_cli.view_planning_requests_workflow(
        {},
        output_fn=output_fn,
    )

    assert result is None
    assert "No planning requests have been saved yet." in messages
    assert pause_calls == [True]


def test_view_planning_requests_workflow_renders_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goal = build_goal()
    request = build_request(goal)
    messages, output_fn = collect_output()

    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_request_list",
        lambda requests: f"Rendered {len(requests)} request",
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: None,
    )

    goal_planning_cli.view_planning_requests_workflow(
        {
            goal.id: request,
        },
        output_fn=output_fn,
    )

    assert "Rendered 1 request" in messages


def test_analyze_all_goals_workflow_handles_empty_goals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages, output_fn = collect_output()
    pause_calls: list[bool] = []

    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: pause_calls.append(True),
    )

    result = goal_planning_cli.analyze_all_goals_workflow(
        [],
        requests_by_goal_id={},
        today=date(2027, 1, 1),
        output_fn=output_fn,
    )

    assert result is None
    assert "No financial goals are available." in messages
    assert "Create at least one goal before using the planner." in messages
    assert pause_calls == [True]


def test_analyze_single_goal_workflow_handles_empty_goals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages, output_fn = collect_output()

    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: None,
    )

    result = goal_planning_cli.analyze_single_goal_workflow(
        [],
        requests_by_goal_id={},
        today=date(2027, 1, 1),
        output_fn=output_fn,
    )

    assert result is None
    assert "No financial goals are available." in messages


def test_monthly_allocation_workflow_handles_empty_goals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages, output_fn = collect_output()

    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: None,
    )

    result = goal_planning_cli.monthly_allocation_workflow(
        [],
        requests_by_goal_id={},
        today=date(2027, 1, 1),
        output_fn=output_fn,
    )

    assert result is None
    assert "No financial goals are available." in messages


def test_analyze_all_goals_workflow_collects_and_stores_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goals = build_goals()
    request_store: dict[int, GoalPlanningRequest] = {}
    expected_result = cast(
        GoalPlanningResult,
        object(),
    )
    captured_requests: list[GoalPlanningRequest] = []

    monkeypatch.setattr(
        goal_planning_cli,
        "build_goal_planning_request",
        lambda goal, **kwargs: build_request(goal),
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "collect_monthly_budget",
        lambda **kwargs: Decimal("1500.00"),
    )

    def fake_analyze(
        requests: list[GoalPlanningRequest],
        *,
        total_available: Decimal,
        as_of_date: date | None = None,
    ) -> GoalPlanningResult:
        captured_requests.extend(requests)
        assert total_available == Decimal("1500.00")
        assert as_of_date == date(2027, 1, 1)
        return expected_result

    monkeypatch.setattr(
        goal_planning_cli,
        "analyze_planning_requests",
        fake_analyze,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_result",
        lambda result: "Rendered planning result",
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: None,
    )

    result = goal_planning_cli.analyze_all_goals_workflow(
        goals,
        requests_by_goal_id=request_store,
        today=date(2027, 1, 1),
        output_fn=lambda message: None,
    )

    assert result is expected_result
    assert len(captured_requests) == 3
    assert set(request_store) == {
        1,
        2,
        3,
    }


def test_analyze_single_goal_workflow_replaces_existing_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goals = build_goals()
    old_request = build_request(
        goals[1],
        monthly_contribution=Decimal("100.00"),
    )
    new_request = build_request(
        goals[1],
        monthly_contribution=Decimal("700.00"),
    )
    request_store = {
        goals[1].id: old_request,
    }
    expected_result = cast(
        GoalPlanningResult,
        object(),
    )

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_goal_number",
        lambda *args, **kwargs: goals[1],
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "build_goal_planning_request",
        lambda *args, **kwargs: new_request,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "collect_monthly_budget",
        lambda **kwargs: Decimal("700.00"),
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "analyze_planning_requests",
        lambda *args, **kwargs: expected_result,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_result",
        lambda result: "Rendered result",
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: None,
    )

    result = goal_planning_cli.analyze_single_goal_workflow(
        goals,
        requests_by_goal_id=request_store,
        today=date(2027, 1, 1),
        output_fn=lambda message: None,
    )

    assert result is expected_result
    assert request_store[goals[1].id] is new_request


def test_monthly_allocation_workflow_reuses_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goals = build_goals()
    requests = [build_request(goal) for goal in goals]
    request_store = {request.goal.id: request for request in requests}
    expected_result = cast(
        GoalPlanningResult,
        object(),
    )
    captured: dict[str, object] = {}

    def fake_collect_missing(
        supplied_goals: list[Goal],
        *,
        requests_by_goal_id: dict[int, GoalPlanningRequest],
        today: date,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> list[GoalPlanningRequest]:
        del input_fn
        del output_fn
        captured["goals"] = supplied_goals
        captured["request_store"] = requests_by_goal_id
        captured["today"] = today
        return requests

    def fake_analyze(
        supplied_requests: list[GoalPlanningRequest],
        *,
        total_available: Decimal,
        as_of_date: date | None = None,
    ) -> GoalPlanningResult:
        captured["analyzed_requests"] = supplied_requests
        captured["total_available"] = total_available
        captured["as_of_date"] = as_of_date
        return expected_result

    monkeypatch.setattr(
        goal_planning_cli,
        "collect_missing_planning_requests",
        fake_collect_missing,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "collect_monthly_budget",
        lambda **kwargs: Decimal("1800.00"),
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "analyze_planning_requests",
        fake_analyze,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_result",
        lambda result: "Rendered allocation",
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: None,
    )

    result = goal_planning_cli.monthly_allocation_workflow(
        goals,
        requests_by_goal_id=request_store,
        today=date(2027, 1, 1),
        output_fn=lambda message: None,
    )

    assert result is expected_result
    assert captured["goals"] == goals
    assert captured["request_store"] is request_store
    assert captured["analyzed_requests"] == requests
    assert captured["total_available"] == Decimal("1800.00")
    assert captured["as_of_date"] == date(2027, 1, 1)


@pytest.mark.parametrize(
    (
        "goals",
        "expected",
    ),
    [
        (
            [],
            False,
        ),
        (
            [build_goal()],
            True,
        ),
    ],
)
def test_ensure_goals_exist(
    goals: list[Goal],
    expected: bool,
) -> None:
    messages, output_fn = collect_output()

    result = goal_planning_cli._ensure_goals_exist(
        goals,
        output_fn=output_fn,
    )

    assert result is expected

    if expected:
        assert messages == []
    else:
        assert messages == [
            "No financial goals are available.",
            "Create at least one goal before using the planner.",
        ]


def test_run_goal_planning_menu_routes_to_update_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    choices = iter([5, 7])

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: next(choices),
    )

    def fake_workflow(
        requests_by_goal_id: dict[int, GoalPlanningRequest],
        *,
        today: date,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> None:
        del requests_by_goal_id
        del today
        del input_fn
        del output_fn
        calls.append("update_request")

    monkeypatch.setattr(
        goal_planning_cli,
        "update_planning_request_workflow",
        fake_workflow,
    )

    goal_planning_cli.run_goal_planning_menu(
        build_goals(),
        output_fn=lambda message: None,
        today=date(2027, 1, 1),
    )

    assert calls == ["update_request"]


def test_update_planning_request_workflow_handles_empty_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages, output_fn = collect_output()
    pause_calls: list[bool] = []

    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: pause_calls.append(True),
    )

    result = goal_planning_cli.update_planning_request_workflow(
        {},
        today=date(2027, 1, 1),
        output_fn=output_fn,
    )

    assert result is None
    assert "No planning requests have been saved yet." in messages
    assert pause_calls == [True]


def test_update_planning_request_workflow_keeps_blank_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goal = build_goal()
    original = build_request(goal)
    request_store = {goal.id: original}

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_request_list",
        lambda requests: "Rendered request list",
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_request",
        lambda request: f"Rendered {request.goal.name}",
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: None,
    )

    result = goal_planning_cli.update_planning_request_workflow(
        request_store,
        today=date(2027, 1, 1),
        input_fn=make_input(["", "", ""]),
        output_fn=lambda message: None,
    )

    assert result is not None
    assert result is request_store[goal.id]
    assert result is not original
    assert result.goal is goal
    assert result.target_date == original.target_date
    assert result.planned_monthly_contribution == original.planned_monthly_contribution
    assert result.priority == original.priority


def test_update_planning_request_workflow_replaces_changed_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goal = build_goal()
    original = build_request(goal)
    request_store = {goal.id: original}
    messages, output_fn = collect_output()

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_request_list",
        lambda requests: "Rendered request list",
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_request",
        lambda request: f"Rendered {request.goal.name}",
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: None,
    )

    result = goal_planning_cli.update_planning_request_workflow(
        request_store,
        today=date(2027, 1, 1),
        input_fn=make_input(["2028-06-30", "725.50", "CRITICAL"]),
        output_fn=output_fn,
    )

    assert result is not None
    assert result.goal is goal
    assert result.target_date == date(2028, 6, 30)
    assert result.planned_monthly_contribution == Decimal("725.50")
    assert result.priority == GoalPriority.CRITICAL
    assert request_store[goal.id] is result
    assert "Planning request updated successfully." in messages


def test_prompt_for_updated_date_reprompts_after_invalid_values() -> None:
    messages, output_fn = collect_output()

    result = goal_planning_cli._prompt_for_updated_date(
        date(2027, 12, 31),
        minimum=date(2027, 1, 1),
        input_fn=make_input(["not-a-date", "2026-12-31", "2028-01-31"]),
        output_fn=output_fn,
    )

    assert result == date(2028, 1, 31)
    assert "Enter a valid date in YYYY-MM-DD format." in messages
    assert "Date must be on or after 2027-01-01." in messages


def test_prompt_for_updated_currency_reprompts_after_invalid_values() -> None:
    messages, output_fn = collect_output()

    result = goal_planning_cli._prompt_for_updated_currency(
        Decimal("500.00"),
        input_fn=make_input(["invalid", "-1", "625.555"]),
        output_fn=output_fn,
    )

    assert result == Decimal("625.56")
    assert "Enter a valid monetary amount." in messages
    assert "Monetary amount cannot be negative." in messages


def test_prompt_for_updated_priority_accepts_name_and_number() -> None:
    named_result = goal_planning_cli._prompt_for_updated_priority(
        GoalPriority.HIGH,
        input_fn=make_input(["critical"]),
        output_fn=lambda message: None,
    )
    numbered_result = goal_planning_cli._prompt_for_updated_priority(
        GoalPriority.HIGH,
        input_fn=make_input(["1"]),
        output_fn=lambda message: None,
    )

    assert named_result == GoalPriority.CRITICAL
    assert numbered_result == list(GoalPriority)[0]


def test_run_goal_planning_menu_routes_to_delete_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    choices = iter([6, 7])

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: next(choices),
    )

    def fake_workflow(
        requests_by_goal_id: dict[int, GoalPlanningRequest],
        *,
        input_fn: InputFunction,
        output_fn: OutputFunction,
    ) -> None:
        del requests_by_goal_id
        del input_fn
        del output_fn
        calls.append("delete_request")

    monkeypatch.setattr(
        goal_planning_cli,
        "delete_planning_request_workflow",
        fake_workflow,
    )

    goal_planning_cli.run_goal_planning_menu(
        build_goals(),
        output_fn=lambda message: None,
        today=date(2027, 1, 1),
    )

    assert calls == ["delete_request"]


def test_delete_planning_request_workflow_handles_empty_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages, output_fn = collect_output()
    pause_calls: list[bool] = []

    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: pause_calls.append(True),
    )

    result = goal_planning_cli.delete_planning_request_workflow(
        {},
        output_fn=output_fn,
    )

    assert result is None
    assert "No planning requests have been saved yet." in messages
    assert pause_calls == [True]


def test_delete_planning_request_workflow_deletes_confirmed_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goals = build_goals()
    first_request = build_request(goals[0])
    second_request = build_request(goals[1])
    request_store = {
        goals[0].id: first_request,
        goals[1].id: second_request,
    }
    messages, output_fn = collect_output()

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: 2,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_request_list",
        lambda requests: "Rendered request list",
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: None,
    )

    result = goal_planning_cli.delete_planning_request_workflow(
        request_store,
        input_fn=make_input(["y"]),
        output_fn=output_fn,
    )

    assert result is second_request
    assert goals[0].id in request_store
    assert goals[1].id not in request_store
    assert "Planning request deleted successfully." in messages


def test_delete_planning_request_workflow_cancels_deletion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goal = build_goal()
    request = build_request(goal)
    request_store = {goal.id: request}
    messages, output_fn = collect_output()

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_request_list",
        lambda requests: "Rendered request list",
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: None,
    )

    result = goal_planning_cli.delete_planning_request_workflow(
        request_store,
        input_fn=make_input(["n"]),
        output_fn=output_fn,
    )

    assert result is None
    assert request_store == {goal.id: request}
    assert "Deletion cancelled." in messages


def test_delete_planning_request_workflow_reprompts_invalid_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goal = build_goal()
    request = build_request(goal)
    request_store = {goal.id: request}
    messages, output_fn = collect_output()

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_planning_request_list",
        lambda requests: "Rendered request list",
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "pause",
        lambda **kwargs: None,
    )

    result = goal_planning_cli.delete_planning_request_workflow(
        request_store,
        input_fn=make_input(["maybe", "yes"]),
        output_fn=output_fn,
    )

    assert result is request
    assert request_store == {}
    assert "Enter Y to confirm or N to cancel." in messages
