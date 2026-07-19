"""Tests for goal-planning request persistence."""

import json
from datetime import date

import pytest

from src.financial.application.goal_planning_service import GoalPlanningRequest
from src.financial.goals.allocation import GoalPriority
from src.financial.goals.models import Goal
from src.financial.planning.repository import (
    load_goal_planning_requests_from_file,
    remove_goal_planning_request_from_file,
    save_goal_planning_requests_to_file,
)


def build_goal(goal_id: int = 1) -> Goal:
    return Goal(
        id=goal_id,
        name="Emergency Fund",
        target_amount=10000,
        current_amount=4000,
    )


def build_request(goal: Goal) -> GoalPlanningRequest:
    return GoalPlanningRequest(
        goal=goal,
        target_date=date(2028, 12, 31),
        planned_monthly_contribution=500,
        priority=GoalPriority.HIGH,
    )


def test_save_and_load_goal_planning_requests(tmp_path) -> None:
    goal = build_goal()
    file_path = tmp_path / "planning.json"

    save_goal_planning_requests_to_file(
        {goal.id: build_request(goal)},
        file_path=file_path,
    )
    loaded = load_goal_planning_requests_from_file(
        [goal],
        file_path=file_path,
    )

    assert list(loaded) == [goal.id]
    assert loaded[goal.id].goal is goal
    assert loaded[goal.id].target_date == date(2028, 12, 31)
    assert loaded[goal.id].planned_monthly_contribution == 500
    assert loaded[goal.id].priority == GoalPriority.HIGH


def test_load_ignores_orphaned_goal_requests(tmp_path) -> None:
    file_path = tmp_path / "planning.json"
    file_path.write_text(json.dumps([{
        "goal_id": 99,
        "target_date": "2028-12-31",
        "planned_monthly_contribution": 500,
        "priority": "HIGH",
    }]), encoding="utf-8")

    assert load_goal_planning_requests_from_file([], file_path=file_path) == {}


def test_load_rejects_invalid_json(tmp_path) -> None:
    file_path = tmp_path / "planning.json"
    file_path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid JSON"):
        load_goal_planning_requests_from_file([], file_path=file_path)


def test_remove_goal_planning_request(tmp_path) -> None:
    first_goal = build_goal(1)
    second_goal = Goal(
        id=2,
        name="Vacation",
        target_amount=3000,
        current_amount=500,
    )
    file_path = tmp_path / "planning.json"

    save_goal_planning_requests_to_file({
        first_goal.id: build_request(first_goal),
        second_goal.id: build_request(second_goal),
    }, file_path=file_path)

    assert remove_goal_planning_request_from_file(
        first_goal.id,
        file_path=file_path,
    ) is True

    loaded = load_goal_planning_requests_from_file(
        [first_goal, second_goal],
        file_path=file_path,
    )
    assert list(loaded) == [second_goal.id]
