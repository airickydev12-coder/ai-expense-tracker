from datetime import date
from decimal import Decimal

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
        "target_amount": Decimal("10000.00"),
        "current_amount": Decimal("4000.00"),
        "remaining_amount": Decimal("6000.00"),
        "months_remaining": 12,
        "required_monthly_contribution": Decimal("500.00"),
        "planned_monthly_contribution": Decimal("600.00"),
        "monthly_contribution_difference": Decimal("100.00"),
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
    assert projection.remaining_amount == Decimal("6000.00")
    assert projection.months_remaining == 12
    assert projection.monthly_shortfall == Decimal("0.00")
    assert projection.monthly_surplus == Decimal("100.00")
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
            remaining_amount=Decimal("-1.00"),
        )


def test_goal_projection_calculates_shortfall():
    projection = build_projection(
        required_monthly_contribution=Decimal("500.00"),
        planned_monthly_contribution=Decimal("350.00"),
        monthly_contribution_difference=Decimal("-150.00"),
    )

    assert projection.monthly_shortfall == Decimal("150.00")
    assert projection.monthly_surplus == Decimal("0.00")


def test_goal_projection_identifies_complete_goal():
    projection = build_projection(
        current_amount=Decimal("10000.00"),
        remaining_amount=Decimal("0.00"),
        required_monthly_contribution=Decimal("0.00"),
        monthly_contribution_difference=Decimal("600.00"),
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
        required_monthly_contribution=Decimal("6000.00"),
        monthly_contribution_difference=Decimal("-5400.00"),
    )

    assert projection.has_deadline_passed is True


def test_goal_projection_to_dict():
    projection = build_projection()

    result = projection.to_dict()

    assert result["goal_id"] == 1
    assert result["goal_name"] == "Emergency Fund"
    assert result["as_of_date"] == "2026-07-16"
    assert result["target_date"] == "2027-07-16"

    # Monetary values are serialized with money_to_json().
    assert result["monthly_shortfall"] == "0.00"
    assert result["monthly_surplus"] == "100.00"

    assert result["projected_completion_date"] == "2027-05-16"


def test_goal_feasibility_assessment_creation():
    assessment = GoalFeasibilityAssessment(
        projection=build_projection(),
        status=GoalFeasibilityStatus.FEASIBLE,
        is_feasible=True,
        summary="The goal is on track.",
        recommendation="Maintain the monthly contribution.",
    )

    assert assessment.status == GoalFeasibilityStatus.FEASIBLE
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
