from datetime import date
from decimal import Decimal

from src.financial.goals.feasibility import (
    assess_goal_feasibility,
)
from src.financial.goals.models import Goal
from src.financial.goals.planning_models import (
    GoalFeasibilityStatus,
)
from src.financial.goals.projections import (
    build_goal_projection,
)


def build_assessment(
    *,
    current_amount: Decimal = Decimal("4000"),
    target_date: date = date(
        2027,
        7,
        16,
    ),
    planned_monthly_contribution: float = 500,
):
    """Build a goal feasibility assessment."""
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000"),
        current_amount=current_amount,
    )

    projection = build_goal_projection(
        goal,
        target_date=target_date,
        planned_monthly_contribution=(planned_monthly_contribution),
        as_of_date=date(
            2026,
            7,
            16,
        ),
    )

    return assess_goal_feasibility(projection)


def test_completed_goal_is_feasible():
    assessment = build_assessment(
        current_amount=Decimal("10000"),
        planned_monthly_contribution=0,
    )

    assert assessment.status == (GoalFeasibilityStatus.COMPLETED)
    assert assessment.is_feasible is True
    assert "fully funded" in assessment.summary


def test_goal_with_sufficient_contribution_is_feasible():
    assessment = build_assessment(
        planned_monthly_contribution=500,
    )

    assert assessment.status == (GoalFeasibilityStatus.FEASIBLE)
    assert assessment.is_feasible is True
    assert "on track" in assessment.summary


def test_goal_with_contribution_surplus_is_feasible():
    assessment = build_assessment(
        planned_monthly_contribution=700,
    )

    assert assessment.status == (GoalFeasibilityStatus.FEASIBLE)
    assert assessment.is_feasible is True


def test_goal_with_insufficient_contribution_is_at_risk():
    assessment = build_assessment(
        planned_monthly_contribution=300,
    )

    assert assessment.status == (GoalFeasibilityStatus.AT_RISK)
    assert assessment.is_feasible is False
    assert "$200.00 per month" in assessment.summary
    assert "$500.00" in assessment.recommendation


def test_goal_without_contribution_is_unfunded():
    assessment = build_assessment(
        planned_monthly_contribution=0,
    )

    assert assessment.status == (GoalFeasibilityStatus.UNFUNDED)
    assert assessment.is_feasible is False
    assert "no monthly contribution" in (assessment.summary)


def test_goal_with_passed_deadline_is_not_feasible():
    assessment = build_assessment(
        target_date=date(
            2026,
            7,
            1,
        ),
        planned_monthly_contribution=500,
    )

    assert assessment.status == (GoalFeasibilityStatus.MISSED_DEADLINE)
    assert assessment.is_feasible is False
    assert "target date has passed" in assessment.summary


def test_feasibility_assessment_to_dict():
    assessment = build_assessment(
        planned_monthly_contribution=500,
    )

    result = assessment.to_dict()

    assert result["status"] == "Feasible"
    assert result["is_feasible"] is True
    assert result["projection"]["goal_name"] == ("Emergency Fund")
