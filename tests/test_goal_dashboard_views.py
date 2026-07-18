"""Tests for financial-goal dashboard rendering."""

from datetime import date

from src.financial.application.goal_dashboard_service import (
    build_goal_dashboard,
)
from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
)
from src.financial.goals.allocation import GoalPriority
from src.financial.goals.models import Goal
from src.presentation.goal_dashboard_views import (
    render_goal_dashboard,
    render_goal_dashboard_item,
)


AS_OF_DATE = date(2027, 1, 1)


def test_render_goal_dashboard_item() -> None:
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=10000,
        current_amount=4000,
    )
    request = GoalPlanningRequest(
        goal=goal,
        target_date=date(2028, 1, 1),
        planned_monthly_contribution=500,
        priority=GoalPriority.HIGH,
    )

    dashboard = build_goal_dashboard(
        [goal],
        requests_by_goal_id={
            goal.id: request,
        },
        as_of_date=AS_OF_DATE,
    )

    output = render_goal_dashboard_item(
        dashboard.items[0]
    )

    assert "1. Emergency Fund" in output
    assert "$4,000.00 of $10,000.00" in output
    assert "40.0%" in output
    assert "On Track" in output
    assert "Priority: High" in output


def test_render_goal_dashboard() -> None:
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=10000,
        current_amount=4000,
    )

    dashboard = build_goal_dashboard(
        [goal],
        as_of_date=AS_OF_DATE,
    )

    output = render_goal_dashboard(dashboard)

    assert "FINANCIAL GOAL DASHBOARD" in output
    assert "Total Goals: 1" in output
    assert "Total Target Amount: $10,000.00" in output
    assert "Total Currently Saved: $4,000.00" in output
    assert "Total Remaining Amount: $6,000.00" in output
    assert "Overall Funding: 40.0%" in output
    assert "Planning Required: 1" in output
    assert "Highest-Priority Goal: Not assigned" in output
    assert "Emergency Fund" in output


def test_render_empty_goal_dashboard() -> None:
    dashboard = build_goal_dashboard(
        [],
        as_of_date=AS_OF_DATE,
    )

    output = render_goal_dashboard(dashboard)

    assert "Total Goals: 0" in output
    assert "No financial goals are available." in output
