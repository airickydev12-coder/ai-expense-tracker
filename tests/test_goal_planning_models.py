from datetime import date

import pytest

from src.financial.goals.planning_models import (
    GoalFeasibilityAssessment,
    GoalFeasibilityStatus,
    GoalProjection,
)


def build_projection(
    **overrides,
) -> GoalProjection:
    """Create a valid goal projection for tests."""
    values = {
        "goal_id": 1,
        "goal_name": "Emergency Fund",
        "as_of_date": date(2026, 7, 16),
        "target_date": date(2027, 7, 16),
        "target_amount": 10000,
        "current_amount": 4000,
        "remaining_amount": 6000,
        "months_remaining": 12,
        "required_monthly_contribution": 500,
        "planned_monthly_contribution": 600,
        "monthly_contribution_difference": 100,
        "projected_completion_date": date(
            2027,
            5,
            16,
        ),
    }

    values.update(overrides)

    return GoalProjection(**values)


def test_goal_projection_creation():
    projection = build_projection()

    assert projection.goal_id == 1
    assert projection.goal_name == "Emergency Fund"
    assert projection.remaining_amount == 6000
    assert projection.months_remaining == 12
    assert projection.monthly_shortfall == 0
    assert projection.monthly_surplus == 100
    assert projection.is_complete is False


def test_goal_projection_normalizes_name():
    projection = build_projection(
        goal_name="  Emergency Fund  ",
    )

    assert projection.goal_name == "Emergency Fund"


def test_goal_projection_rejects_invalid_id():
    with pytest.raises(
        ValueError,
        match="ID",
    ):
        build_projection(
            goal_id=0,
        )


def test_goal_projection_rejects_empty_name():
    with pytest.raises(
        ValueError,
        match="name",
    ):
        build_projection(
            goal_name=" ",
        )


def test_goal_projection_rejects_negative_remaining_amount():
    with pytest.raises(
        ValueError,
        match="remaining",
    ):
        build_projection(
            remaining_amount=-1,
        )


def test_goal_projection_calculates_shortfall():
    projection = build_projection(
        required_monthly_contribution=500,
        planned_monthly_contribution=350,
        monthly_contribution_difference=-150,
    )

    assert projection.monthly_shortfall == 150
    assert projection.monthly_surplus == 0


def test_goal_projection_identifies_complete_goal():
    projection = build_projection(
        current_amount=10000,
        remaining_amount=0,
        required_monthly_contribution=0,
        monthly_contribution_difference=600,
        projected_completion_date=date(
            2026,
            7,
            16,
        ),
    )

    assert projection.is_complete is True
    assert projection.has_deadline_passed is False


def test_goal_projection_identifies_passed_deadline():
    projection = build_projection(
        target_date=date(2026, 7, 1),
        months_remaining=0,
        required_monthly_contribution=6000,
        monthly_contribution_difference=-5400,
    )

    assert projection.has_deadline_passed is True


def test_goal_projection_to_dict():
    projection = build_projection()

    result = projection.to_dict()

    assert result["goal_id"] == 1
    assert result["goal_name"] == "Emergency Fund"
    assert result["as_of_date"] == "2026-07-16"
    assert result["target_date"] == "2027-07-16"
    assert result["monthly_shortfall"] == 0
    assert result["monthly_surplus"] == 100
    assert result["projected_completion_date"] == ("2027-05-16")


def test_goal_feasibility_assessment_creation():
    assessment = GoalFeasibilityAssessment(
        projection=build_projection(),
        status=GoalFeasibilityStatus.FEASIBLE,
        is_feasible=True,
        summary="The goal is on track.",
        recommendation=("Maintain the monthly contribution."),
    )

    assert assessment.status == (GoalFeasibilityStatus.FEASIBLE)
    assert assessment.is_feasible is True


def test_goal_feasibility_assessment_rejects_empty_summary():
    with pytest.raises(
        ValueError,
        match="summary",
    ):
        GoalFeasibilityAssessment(
            projection=build_projection(),
            status=GoalFeasibilityStatus.FEASIBLE,
            is_feasible=True,
            summary=" ",
            recommendation="Maintain the plan.",
        )


def test_goal_feasibility_assessment_to_dict():
    assessment = GoalFeasibilityAssessment(
        projection=build_projection(),
        status=GoalFeasibilityStatus.FEASIBLE,
        is_feasible=True,
        summary="The goal is on track.",
        recommendation="Maintain the plan.",
    )

    result = assessment.to_dict()

    assert result["status"] == "Feasible"
    assert result["is_feasible"] is True
    assert result["projection"]["goal_id"] == 1
