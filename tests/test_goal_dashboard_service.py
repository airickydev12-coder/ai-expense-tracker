"""Tests for the financial-goal dashboard service."""

from datetime import date
from decimal import Decimal

import pytest

from src.financial.application.goal_dashboard_service import (
    GoalDashboardStatus,
    build_goal_dashboard,
)
from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
)
from src.financial.goals.allocation import GoalPriority
from src.financial.goals.models import Goal


AS_OF_DATE = date(2027, 1, 1)


from decimal import Decimal


def build_goal(
    *,
    goal_id: int,
    name: str,
    target_amount: Decimal,
    current_amount: Decimal,
) -> Goal:
    """Build a dashboard test goal."""
    return Goal(
        id=goal_id,
        name=name,
        target_amount=target_amount,
        current_amount=current_amount,
    )


def build_request(
    goal: Goal,
    *,
    target_date: date,
    monthly_contribution: float,
    priority: GoalPriority,
) -> GoalPlanningRequest:
    """Build a dashboard planning request."""
    return GoalPlanningRequest(
        goal=goal,
        target_date=target_date,
        planned_monthly_contribution=monthly_contribution,
        priority=priority,
    )


def test_build_goal_dashboard_without_goals() -> None:
    dashboard = build_goal_dashboard(
        [],
        as_of_date=AS_OF_DATE,
    )

    assert dashboard.total_goals == 0
    assert dashboard.total_target_amount == 0
    assert dashboard.total_current_amount == 0
    assert dashboard.total_remaining_amount == 0
    assert dashboard.overall_funding_percentage == 0
    assert dashboard.highest_priority_goal is None


def test_build_goal_dashboard_calculates_portfolio_totals() -> None:
    goals = [
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
            current_amount=Decimal("3000.00"),
        ),
    ]

    dashboard = build_goal_dashboard(
        goals,
        as_of_date=AS_OF_DATE,
    )

    assert dashboard.total_goals == 2
    assert dashboard.total_target_amount == 13000
    assert dashboard.total_current_amount == 7000
    assert dashboard.total_remaining_amount == 6000
    assert dashboard.overall_funding_percentage == pytest.approx(53.8461538)
    assert dashboard.completed_goals == 1
    assert dashboard.planning_required_goals == 1


def test_build_goal_dashboard_uses_feasibility_statuses() -> None:
    feasible_goal = build_goal(
        goal_id=1,
        name="Emergency Fund",
        target_amount=Decimal("12000.00"),
        current_amount=Decimal("6000.00"),
    )
    unfunded_goal = build_goal(
        goal_id=2,
        name="Car Fund",
        target_amount=Decimal("12000.00"),
        current_amount=Decimal("3000.00"),
    )

    requests = {
        1: build_request(
            feasible_goal,
            target_date=date(2028, 1, 1),
            monthly_contribution=500,
            priority=GoalPriority.HIGH,
        ),
        2: build_request(
            unfunded_goal,
            target_date=date(2028, 1, 1),
            monthly_contribution=0,
            priority=GoalPriority.CRITICAL,
        ),
    }

    dashboard = build_goal_dashboard(
        [
            feasible_goal,
            unfunded_goal,
        ],
        requests_by_goal_id=requests,
        as_of_date=AS_OF_DATE,
    )

    statuses = {item.goal_id: item.status for item in dashboard.items}

    assert statuses[1] == GoalDashboardStatus.ON_TRACK
    assert statuses[2] == GoalDashboardStatus.UNFUNDED
    assert dashboard.on_track_goals == 1
    assert dashboard.unfunded_goals == 1


def test_build_goal_dashboard_selects_highest_priority_goal() -> None:
    high_goal = build_goal(
        goal_id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("4000.00"),
    )
    critical_goal = build_goal(
        goal_id=2,
        name="Debt Payoff",
        target_amount=Decimal("8000.00"),
        current_amount=Decimal("2000.00"),
    )

    requests = {
        1: build_request(
            high_goal,
            target_date=date(2028, 1, 1),
            monthly_contribution=500,
            priority=GoalPriority.HIGH,
        ),
        2: build_request(
            critical_goal,
            target_date=date(2028, 1, 1),
            monthly_contribution=500,
            priority=GoalPriority.CRITICAL,
        ),
    }

    dashboard = build_goal_dashboard(
        [
            high_goal,
            critical_goal,
        ],
        requests_by_goal_id=requests,
        as_of_date=AS_OF_DATE,
    )

    assert dashboard.highest_priority_goal is not None
    assert dashboard.highest_priority_goal.goal_id == 2


def test_build_goal_dashboard_rejects_duplicate_goal_ids() -> None:
    goals = [
        build_goal(
            goal_id=1,
            name="Goal One",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("100.00"),
        ),
        build_goal(
            goal_id=1,
            name="Goal Two",
            target_amount=Decimal("2000.00"),
            current_amount=Decimal("200.00"),
        ),
    ]

    with pytest.raises(
        ValueError,
        match="duplicate goal IDs",
    ):
        build_goal_dashboard(
            goals,
            as_of_date=AS_OF_DATE,
        )


def test_build_goal_dashboard_rejects_mismatched_request_key() -> None:
    goal = build_goal(
        goal_id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("4000.00"),
    )
    request = build_request(
        goal,
        target_date=date(2028, 1, 1),
        monthly_contribution=500,
        priority=GoalPriority.HIGH,
    )

    with pytest.raises(
        ValueError,
        match="key must match",
    ):
        build_goal_dashboard(
            [goal],
            requests_by_goal_id={
                99: request,
            },
            as_of_date=AS_OF_DATE,
        )
