from datetime import date

import pytest

from src.financial.goals.allocation import (
    GoalAllocation,
    GoalAllocationPlan,
    GoalFundingRequest,
    GoalPriority,
    allocate_goal_funding,
    prioritize_goal_funding_requests,
)
from src.financial.goals.models import Goal
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
    goal_id: int,
    name: str,
    target_amount: float,
    current_amount: float,
    target_date: date,
    priority: GoalPriority,
    planned_monthly_contribution: float = 0,
) -> GoalFundingRequest:
    """Build a valid funding request for tests."""
    goal = Goal(
        id=goal_id,
        name=name,
        target_amount=target_amount,
        current_amount=current_amount,
    )

    projection = build_goal_projection(
        goal,
        target_date=target_date,
        planned_monthly_contribution=(planned_monthly_contribution),
        as_of_date=AS_OF_DATE,
    )

    return GoalFundingRequest(
        projection=projection,
        priority=priority,
    )


def build_standard_requests() -> list[GoalFundingRequest]:
    """Build three requests with monthly requirements."""
    return [
        build_request(
            goal_id=1,
            name="Emergency Fund",
            target_amount=10000,
            current_amount=5200,
            target_date=date(
                2027,
                7,
                18,
            ),
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
            priority=GoalPriority.HIGH,
        ),
    ]


def test_goal_priority_order():
    assert GoalPriority.CRITICAL > GoalPriority.HIGH
    assert GoalPriority.HIGH > GoalPriority.MEDIUM
    assert GoalPriority.MEDIUM > GoalPriority.LOW


def test_goal_funding_request_to_dict():
    request = build_standard_requests()[0]

    result = request.to_dict()

    assert result["priority"] == "CRITICAL"
    assert result["projection"]["goal_id"] == 1


def test_goal_allocation_creation():
    allocation = GoalAllocation(
        goal_id=1,
        goal_name="Emergency Fund",
        priority=GoalPriority.CRITICAL,
        required_amount=400,
        allocated_amount=300,
    )

    assert allocation.goal_id == 1
    assert allocation.required_amount == 400
    assert allocation.allocated_amount == 300
    assert allocation.shortfall == 100
    assert allocation.surplus == 0
    assert allocation.is_fully_funded is False


def test_goal_allocation_normalizes_name():
    allocation = GoalAllocation(
        goal_id=1,
        goal_name="  Emergency Fund  ",
        priority=GoalPriority.HIGH,
        required_amount=400,
        allocated_amount=400,
    )

    assert allocation.goal_name == "Emergency Fund"


def test_goal_allocation_rejects_invalid_id():
    with pytest.raises(
        ValueError,
        match="ID",
    ):
        GoalAllocation(
            goal_id=0,
            goal_name="Emergency Fund",
            priority=GoalPriority.HIGH,
            required_amount=400,
            allocated_amount=400,
        )


def test_goal_allocation_rejects_empty_name():
    with pytest.raises(
        ValueError,
        match="name",
    ):
        GoalAllocation(
            goal_id=1,
            goal_name=" ",
            priority=GoalPriority.HIGH,
            required_amount=400,
            allocated_amount=400,
        )


def test_goal_allocation_rejects_negative_required_amount():
    with pytest.raises(
        ValueError,
        match="required",
    ):
        GoalAllocation(
            goal_id=1,
            goal_name="Emergency Fund",
            priority=GoalPriority.HIGH,
            required_amount=-1,
            allocated_amount=0,
        )


def test_goal_allocation_rejects_negative_allocated_amount():
    with pytest.raises(
        ValueError,
        match="allocated",
    ):
        GoalAllocation(
            goal_id=1,
            goal_name="Emergency Fund",
            priority=GoalPriority.HIGH,
            required_amount=400,
            allocated_amount=-1,
        )


def test_goal_allocation_identifies_fully_funded_goal():
    allocation = GoalAllocation(
        goal_id=1,
        goal_name="Emergency Fund",
        priority=GoalPriority.HIGH,
        required_amount=400,
        allocated_amount=400,
    )

    assert allocation.shortfall == 0
    assert allocation.is_fully_funded is True


def test_goal_allocation_calculates_surplus():
    allocation = GoalAllocation(
        goal_id=1,
        goal_name="Emergency Fund",
        priority=GoalPriority.HIGH,
        required_amount=400,
        allocated_amount=450,
    )

    assert allocation.shortfall == 0
    assert allocation.surplus == 50
    assert allocation.is_fully_funded is True


def test_goal_allocation_to_dict():
    allocation = GoalAllocation(
        goal_id=1,
        goal_name="Emergency Fund",
        priority=GoalPriority.CRITICAL,
        required_amount=400,
        allocated_amount=300,
    )

    result = allocation.to_dict()

    assert result == {
        "goal_id": 1,
        "goal_name": "Emergency Fund",
        "priority": "CRITICAL",
        "required_amount": 400,
        "allocated_amount": 300,
        "shortfall": 100,
        "surplus": 0,
        "is_fully_funded": False,
    }


def test_prioritize_requests_by_priority():
    requests = build_standard_requests()

    prioritized = prioritize_goal_funding_requests(requests)

    assert [request.projection.goal_id for request in prioritized] == [1, 3, 2]


def test_prioritize_same_priority_by_earliest_deadline():
    later_goal = build_request(
        goal_id=1,
        name="Later Goal",
        target_amount=6000,
        current_amount=0,
        target_date=date(
            2027,
            7,
            18,
        ),
        priority=GoalPriority.HIGH,
    )

    earlier_goal = build_request(
        goal_id=2,
        name="Earlier Goal",
        target_amount=6000,
        current_amount=0,
        target_date=date(
            2027,
            1,
            18,
        ),
        priority=GoalPriority.HIGH,
    )

    prioritized = prioritize_goal_funding_requests(
        [
            later_goal,
            earlier_goal,
        ]
    )

    assert [request.projection.goal_id for request in prioritized] == [2, 1]


def test_prioritize_same_priority_and_date_by_requirement():
    smaller_requirement = build_request(
        goal_id=1,
        name="Smaller Goal",
        target_amount=2400,
        current_amount=0,
        target_date=date(
            2027,
            7,
            18,
        ),
        priority=GoalPriority.HIGH,
    )

    larger_requirement = build_request(
        goal_id=2,
        name="Larger Goal",
        target_amount=6000,
        current_amount=0,
        target_date=date(
            2027,
            7,
            18,
        ),
        priority=GoalPriority.HIGH,
    )

    prioritized = prioritize_goal_funding_requests(
        [
            smaller_requirement,
            larger_requirement,
        ]
    )

    assert [request.projection.goal_id for request in prioritized] == [2, 1]


def test_allocate_goal_funding_by_priority():
    plan = allocate_goal_funding(
        build_standard_requests(),
        total_available=700,
    )

    emergency = plan.get_allocation_by_goal_id(1)
    car = plan.get_allocation_by_goal_id(3)
    vacation = plan.get_allocation_by_goal_id(2)

    assert emergency is not None
    assert car is not None
    assert vacation is not None

    assert emergency.required_amount == 400
    assert emergency.allocated_amount == 400

    assert car.required_amount == 600
    assert car.allocated_amount == 300

    assert vacation.required_amount == 300
    assert vacation.allocated_amount == 0


def test_allocate_goal_funding_when_all_goals_can_be_funded():
    plan = allocate_goal_funding(
        build_standard_requests(),
        total_available=1500,
    )

    assert plan.total_required == 1300
    assert plan.total_allocated == 1300
    assert plan.total_shortfall == 0
    assert plan.remaining_cash == 200
    assert plan.all_goals_funded is True


def test_allocate_goal_funding_with_partial_funding():
    plan = allocate_goal_funding(
        build_standard_requests(),
        total_available=1000,
    )

    assert plan.total_required == 1300
    assert plan.total_allocated == 1000
    assert plan.total_shortfall == 300
    assert plan.remaining_cash == 0
    assert plan.all_goals_funded is False


def test_allocate_goal_funding_with_no_available_cash():
    plan = allocate_goal_funding(
        build_standard_requests(),
        total_available=0,
    )

    assert plan.total_allocated == 0
    assert plan.total_shortfall == 1300
    assert plan.remaining_cash == 0
    assert plan.all_goals_funded is False


def test_allocate_goal_funding_with_no_requests():
    plan = allocate_goal_funding(
        [],
        total_available=1000,
    )

    assert plan.allocations == []
    assert plan.total_required == 0
    assert plan.total_allocated == 0
    assert plan.total_shortfall == 0
    assert plan.remaining_cash == 1000
    assert plan.all_goals_funded is True


def test_allocate_goal_funding_does_not_modify_requests():
    requests = build_standard_requests()
    original_ids = [request.projection.goal_id for request in requests]

    allocate_goal_funding(
        requests,
        total_available=700,
    )

    assert [request.projection.goal_id for request in requests] == original_ids


def test_allocate_goal_funding_rejects_negative_total():
    with pytest.raises(
        ValueError,
        match="available",
    ):
        allocate_goal_funding(
            build_standard_requests(),
            total_available=-1,
        )


def test_allocate_goal_funding_rejects_duplicate_goal_ids():
    request = build_standard_requests()[0]

    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        allocate_goal_funding(
            [
                request,
                request,
            ],
            total_available=1000,
        )


def test_goal_allocation_plan_returns_defensive_copy():
    plan = allocate_goal_funding(
        build_standard_requests(),
        total_available=1000,
    )

    returned_allocations = plan.allocations
    returned_allocations.clear()

    assert len(plan.allocations) == 3


def test_goal_allocation_plan_rejects_duplicate_goal_ids():
    allocation = GoalAllocation(
        goal_id=1,
        goal_name="Emergency Fund",
        priority=GoalPriority.HIGH,
        required_amount=400,
        allocated_amount=400,
    )

    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        GoalAllocationPlan(
            allocations=[
                allocation,
                allocation,
            ],
            total_available=1000,
        )


def test_goal_allocation_plan_to_dict():
    plan = allocate_goal_funding(
        build_standard_requests(),
        total_available=1500,
    )

    result = plan.to_dict()

    assert len(result["allocations"]) == 3
    assert result["total_available"] == 1500
    assert result["total_required"] == 1300
    assert result["total_allocated"] == 1300
    assert result["total_shortfall"] == 0
    assert result["remaining_cash"] == 200
    assert result["all_goals_funded"] is True
