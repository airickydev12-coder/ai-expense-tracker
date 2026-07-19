"""Persistence integration tests for the Goal Planner CLI."""

from datetime import date
from decimal import Decimal
import decimal

import pytest

from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
)
from src.financial.goals.allocation import GoalPriority
from src.financial.goals.models import Goal
from src.financial.planning.repository import (
    load_goal_planning_requests_from_file,
    save_goal_planning_requests_to_file,
)
from src.presentation import goal_planning_cli


def test_goal_planning_menu_loads_persisted_requests(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("4000.00"),
    )
    request = GoalPlanningRequest(
        goal=goal,
        target_date=date(2028, 12, 31),
        planned_monthly_contribution=500,
        priority=GoalPriority.HIGH,
    )

    file_path = tmp_path / "planning.json"
    save_goal_planning_requests_to_file(
        {goal.id: request},
        file_path=file_path,
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        goal_planning_cli,
        "build_goal_dashboard",
        lambda goals, **kwargs: (
            captured.update(
                requests=kwargs["requests_by_goal_id"],
            )
            or object()
        ),
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_dashboard",
        lambda dashboard: "Dashboard",
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: 6,
    )

    goal_planning_cli.run_goal_planning_menu(
        [goal],
        output_fn=lambda message: None,
        today=date(2027, 1, 1),
        planning_file_path=file_path,
    )

    requests = captured["requests"]

    assert isinstance(requests, dict)
    assert requests[goal.id].planned_monthly_contribution == 500


def test_goal_planning_menu_saves_new_request(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("4000.00"),
    )
    file_path = tmp_path / "planning.json"
    choices = iter([2, 6])

    monkeypatch.setattr(
        goal_planning_cli,
        "prompt_for_menu_choice",
        lambda *args, **kwargs: next(choices),
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "build_goal_dashboard",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        goal_planning_cli,
        "render_goal_dashboard",
        lambda dashboard: "Dashboard",
    )

    def fake_workflow(
        goals,
        *,
        requests_by_goal_id,
        today,
        input_fn,
        output_fn,
    ):
        del goals, today, input_fn, output_fn

        requests_by_goal_id[goal.id] = GoalPlanningRequest(
            goal=goal,
            target_date=date(2028, 12, 31),
            planned_monthly_contribution=750,
            priority=GoalPriority.CRITICAL,
        )

    monkeypatch.setattr(
        goal_planning_cli,
        "analyze_single_goal_workflow",
        fake_workflow,
    )

    goal_planning_cli.run_goal_planning_menu(
        [goal],
        output_fn=lambda message: None,
        today=date(2027, 1, 1),
        planning_file_path=file_path,
    )

    loaded = load_goal_planning_requests_from_file(
        [goal],
        file_path=file_path,
    )

    assert loaded[goal.id].planned_monthly_contribution == 750
    assert loaded[goal.id].priority == GoalPriority.CRITICAL
