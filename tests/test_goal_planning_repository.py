"""Tests for goal-planning request persistence."""

from datetime import date
from decimal import Decimal

import pytest

from src.core.db import get_connection
from src.financial.application.goal_planning_service import GoalPlanningRequest
from src.financial.goals.allocation import GoalPriority
from src.financial.goals.models import Goal
from src.financial.planning.repository import (
    load_goal_planning_requests_from_file,
    remove_goal_planning_request_from_file,
    save_goal_planning_requests_to_file,
)

USER_ID = 1


def build_goal(goal_id: int = 1) -> Goal:
    return Goal(
        id=goal_id,
        name="Emergency Fund",
        target_amount=Decimal("10000"),
        current_amount=Decimal("4000"),
    )


def build_request(goal: Goal) -> GoalPlanningRequest:
    return GoalPlanningRequest(
        goal=goal,
        target_date=date(2028, 12, 31),
        planned_monthly_contribution=500,
        priority=GoalPriority.HIGH,
    )


def test_save_and_load_goal_planning_requests(db_path) -> None:
    goal = build_goal()

    save_goal_planning_requests_to_file(
        {goal.id: build_request(goal)},
        USER_ID,
        file_path=db_path,
    )
    loaded = load_goal_planning_requests_from_file(
        USER_ID,
        [goal],
        file_path=db_path,
    )

    assert list(loaded) == [goal.id]
    assert loaded[goal.id].goal is goal
    assert loaded[goal.id].target_date == date(2028, 12, 31)
    assert loaded[goal.id].planned_monthly_contribution == 500
    assert loaded[goal.id].priority == GoalPriority.HIGH


def test_load_ignores_orphaned_goal_requests(db_path) -> None:
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO goal_planning_requests (
                goal_id, target_date, planned_monthly_contribution, priority, user_id
            )
            VALUES (99, '2028-12-31', '500.00', 'HIGH', ?)
            """,
            (USER_ID,),
        )

    assert load_goal_planning_requests_from_file(USER_ID, [], file_path=db_path) == {}


def test_load_rejects_invalid_database_file(
    tmp_path,
) -> None:
    db_path = tmp_path / "planning.db"
    db_path.write_text("not a valid sqlite database", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="Failed to load goal planning requests",
    ):
        load_goal_planning_requests_from_file(USER_ID, [], file_path=db_path)


def test_remove_goal_planning_request(db_path) -> None:
    first_goal = build_goal(1)
    second_goal = Goal(
        id=2,
        name="Vacation",
        target_amount=Decimal("3000"),
        current_amount=Decimal("500"),
    )

    save_goal_planning_requests_to_file(
        {
            first_goal.id: build_request(first_goal),
            second_goal.id: build_request(second_goal),
        },
        USER_ID,
        file_path=db_path,
    )

    assert (
        remove_goal_planning_request_from_file(
            USER_ID,
            first_goal.id,
            file_path=db_path,
        )
        is True
    )

    loaded = load_goal_planning_requests_from_file(
        USER_ID,
        [first_goal, second_goal],
        file_path=db_path,
    )
    assert list(loaded) == [second_goal.id]
