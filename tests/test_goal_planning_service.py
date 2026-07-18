from datetime import date

import pytest

from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
    GoalPlanningResult,
    allocate_monthly_funding,
    analyze_goals,
    assess_goal,
    build_projection,
)
from src.financial.goals.allocation import (
    GoalPriority,
)
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


AS_OF_DATE = date(
    2026,
    7,
    18,
)


def build_request(
    *,
    goal_id: int = 1,
    name: str = "Emergency Fund",
    target_amount: float = 10000,
    current_amount: float = 4000,
    target_date: date = date(
        2027,
        7,
        18,
    ),
    planned_monthly_contribution: float = 500,
    priority: GoalPriority = GoalPriority.HIGH,
) -> GoalPlanningRequest:
    """Create a valid goal-planning request."""
    return GoalPlanningRequest(
        goal=Goal(
            id=goal_id,
            name=name,
            target_amount=target_amount,
            current_amount=current_amount,
        ),
        target_date=target_date,
        planned_monthly_contribution=(planned_monthly_contribution),
        priority=priority,
    )


def build_standard_requests() -> list[GoalPlanningRequest]:
    """Create a representative collection of planning requests."""
    return [
        build_request(
            goal_id=1,
            name="Emergency Fund",
            target_amount=10000,
            current_amount=4000,
            target_date=date(
                2027,
                7,
                18,
            ),
            planned_monthly_contribution=500,
            priority=GoalPriority.CRITICAL,
        ),
        build_request(
            goal_id=2,
            name="Vacation",
            target_amount=3000,
            current_amount=600,
            target_date=date(
                2027,
                3,
                18,
            ),
            planned_monthly_contribution=200,
            priority=GoalPriority.LOW,
        ),
        build_request(
            goal_id=3,
            name="Car Fund",
            target_amount=12000,
            current_amount=4800,
            target_date=date(
                2027,
                7,
                18,
            ),
            planned_monthly_contribution=0,
            priority=GoalPriority.HIGH,
        ),
    ]


def test_goal_planning_request_creation():
    request = build_request()

    assert request.goal.id == 1
    assert request.target_date == date(
        2027,
        7,
        18,
    )
    assert request.planned_monthly_contribution == 500
    assert request.priority == GoalPriority.HIGH


def test_goal_planning_request_rejects_negative_contribution():
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        build_request(
            planned_monthly_contribution=-1,
        )


def test_goal_planning_request_rejects_invalid_priority():
    with pytest.raises(
        TypeError,
        match="GoalPriority",
    ):
        GoalPlanningRequest(
            goal=Goal(
                id=1,
                name="Emergency Fund",
                target_amount=10000,
                current_amount=4000,
            ),
            target_date=date(
                2027,
                7,
                18,
            ),
            planned_monthly_contribution=500,
            priority="HIGH",  # type: ignore[arg-type]
        )


def test_goal_planning_request_to_dict():
    result = build_request().to_dict()

    assert result["goal"]["id"] == 1
    assert result["target_date"] == "2027-07-18"
    assert result["planned_monthly_contribution"] == 500
    assert result["priority"] == "HIGH"


def test_build_projection():
    projection = build_projection(
        build_request(),
        as_of_date=AS_OF_DATE,
    )

    assert projection.goal_id == 1
    assert projection.remaining_amount == 6000
    assert projection.months_remaining == 12
    assert projection.required_monthly_contribution == 500
    assert projection.planned_monthly_contribution == 500


def test_assess_goal():
    assessment = assess_goal(
        build_request(),
        as_of_date=AS_OF_DATE,
    )

    assert assessment.status == (GoalFeasibilityStatus.FEASIBLE)
    assert assessment.is_feasible is True


def test_allocate_monthly_funding():
    plan = allocate_monthly_funding(
        build_standard_requests(),
        total_available=800,
        as_of_date=AS_OF_DATE,
    )

    emergency = plan.get_allocation_by_goal_id(1)
    car = plan.get_allocation_by_goal_id(3)
    vacation = plan.get_allocation_by_goal_id(2)

    assert emergency is not None
    assert car is not None
    assert vacation is not None

    assert emergency.required_amount == 500
    assert emergency.allocated_amount == 500

    assert car.required_amount == 600
    assert car.allocated_amount == 300

    assert vacation.required_amount == 300
    assert vacation.allocated_amount == 0


def test_allocate_monthly_funding_rejects_duplicate_goals():
    request = build_request()

    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        allocate_monthly_funding(
            [
                request,
                request,
            ],
            total_available=1000,
            as_of_date=AS_OF_DATE,
        )


def test_analyze_goals():
    result = analyze_goals(
        build_standard_requests(),
        total_available=1000,
        as_of_date=AS_OF_DATE,
    )

    assert isinstance(
        result,
        GoalPlanningResult,
    )
    assert result.total_goals == 3
    assert len(result.projections) == 3
    assert len(result.assessments) == 3
    assert len(result.allocation_plan.allocations) == 3


def test_analyze_goals_summary_counts():
    result = analyze_goals(
        build_standard_requests(),
        total_available=1000,
        as_of_date=AS_OF_DATE,
    )

    assert result.completed_goals == 0
    assert result.feasible_goals == 1
    assert result.at_risk_goals == 1
    assert result.unfunded_goals == 1
    assert result.missed_deadline_goals == 0
    assert result.all_goals_feasible is False


def test_analyze_goals_funding_summary():
    result = analyze_goals(
        build_standard_requests(),
        total_available=1000,
        as_of_date=AS_OF_DATE,
    )

    assert result.total_monthly_required == 1400
    assert result.total_monthly_allocated == 1000
    assert result.overall_funding_gap == 400
    assert result.remaining_monthly_cash == 0


def test_analyze_completed_goal():
    request = build_request(
        current_amount=10000,
        planned_monthly_contribution=0,
    )

    result = analyze_goals(
        [request],
        total_available=500,
        as_of_date=AS_OF_DATE,
    )

    assert result.completed_goals == 1
    assert result.feasible_goals == 0
    assert result.all_goals_feasible is True
    assert result.total_monthly_required == 0
    assert result.remaining_monthly_cash == 500


def test_analyze_goals_with_no_requests():
    result = analyze_goals(
        [],
        total_available=1000,
        as_of_date=AS_OF_DATE,
    )

    assert result.total_goals == 0
    assert result.projections == []
    assert result.assessments == []
    assert result.total_monthly_required == 0
    assert result.total_monthly_allocated == 0
    assert result.overall_funding_gap == 0
    assert result.remaining_monthly_cash == 1000
    assert result.all_goals_feasible is True


def test_analyze_goals_rejects_negative_available_funding():
    with pytest.raises(
        ValueError,
        match="available",
    ):
        analyze_goals(
            build_standard_requests(),
            total_available=-1,
            as_of_date=AS_OF_DATE,
        )


def test_analyze_goals_rejects_duplicate_goal_ids():
    request = build_request()

    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        analyze_goals(
            [
                request,
                request,
            ],
            total_available=1000,
            as_of_date=AS_OF_DATE,
        )


def test_goal_planning_result_returns_defensive_copies():
    result = analyze_goals(
        build_standard_requests(),
        total_available=1000,
        as_of_date=AS_OF_DATE,
    )

    returned_projections = result.projections
    returned_assessments = result.assessments

    returned_projections.clear()
    returned_assessments.clear()

    assert len(result.projections) == 3
    assert len(result.assessments) == 3


def test_goal_planning_result_get_projection_by_id():
    result = analyze_goals(
        build_standard_requests(),
        total_available=1000,
        as_of_date=AS_OF_DATE,
    )

    projection = result.get_projection_by_goal_id(2)

    assert projection is not None
    assert projection.goal_name == "Vacation"
    assert result.get_projection_by_goal_id(999) is None


def test_goal_planning_result_get_assessment_by_id():
    result = analyze_goals(
        build_standard_requests(),
        total_available=1000,
        as_of_date=AS_OF_DATE,
    )

    assessment = result.get_assessment_by_goal_id(3)

    assert assessment is not None
    assert assessment.status == (GoalFeasibilityStatus.UNFUNDED)
    assert result.get_assessment_by_goal_id(999) is None


def test_goal_planning_result_rejects_mismatched_ids():
    request = build_request()

    projection = build_goal_projection(
        request.goal,
        target_date=request.target_date,
        planned_monthly_contribution=(request.planned_monthly_contribution),
        as_of_date=AS_OF_DATE,
    )

    assessment = assess_goal_feasibility(projection)

    different_projection = build_goal_projection(
        Goal(
            id=2,
            name="Vacation",
            target_amount=3000,
            current_amount=500,
        ),
        target_date=date(
            2027,
            7,
            18,
        ),
        planned_monthly_contribution=250,
        as_of_date=AS_OF_DATE,
    )

    allocation_plan = allocate_monthly_funding(
        [request],
        total_available=500,
        as_of_date=AS_OF_DATE,
    )

    with pytest.raises(
        ValueError,
        match="same goal IDs",
    ):
        GoalPlanningResult(
            projections=[
                different_projection,
            ],
            assessments=[
                assessment,
            ],
            allocation_plan=allocation_plan,
        )


def test_goal_planning_result_to_dict():
    result = analyze_goals(
        build_standard_requests(),
        total_available=1000,
        as_of_date=AS_OF_DATE,
    )

    data = result.to_dict()

    assert len(data["projections"]) == 3
    assert len(data["assessments"]) == 3
    assert len(data["allocation_plan"]["allocations"]) == 3

    summary = data["summary"]

    assert summary["total_goals"] == 3
    assert summary["feasible_goals"] == 1
    assert summary["at_risk_goals"] == 1
    assert summary["unfunded_goals"] == 1
    assert summary["total_monthly_required"] == 1400
    assert summary["total_monthly_allocated"] == 1000
    assert summary["overall_funding_gap"] == 400
