"""Tests for planning-request cleanup when a goal is deleted."""

from datetime import date

from src.financial.application.goal_planning_service import GoalPlanningRequest
from src.financial.goals import service
from src.financial.goals.allocation import GoalPriority
from src.financial.planning.repository import (
    load_goal_planning_requests_from_file,
    save_goal_planning_requests_to_file,
)


def test_delete_goal_removes_planning_request(tmp_path) -> None:
    goals_file = tmp_path / "goals.json"
    planning_file = tmp_path / "goal_planning_requests.json"

    service.goals.clear()
    goal = service.add_goal(
        "Emergency Fund",
        10000,
        4000,
        file_path=goals_file,
    )

    save_goal_planning_requests_to_file(
        {
            goal.id: GoalPlanningRequest(
                goal=goal,
                target_date=date(2028, 12, 31),
                planned_monthly_contribution=500,
                priority=GoalPriority.HIGH,
            )
        },
        file_path=planning_file,
    )

    deleted = service.delete_goal(goal.id, file_path=goals_file)
    loaded = load_goal_planning_requests_from_file([], file_path=planning_file)

    assert deleted is not None
    assert loaded == {}
    service.goals.clear()
