from datetime import date
from decimal import Decimal

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
    target_amount: Decimal,
    current_amount: Decimal,
    target_date: date,
    priority: GoalPriority,
    planned_monthly_contribution: Decimal = Decimal("0.00"),
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
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("5200.00"),
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
            target_amount=Decimal("3000.00"),
            current_amount=Decimal("600.00"),
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
            target_amount=Decimal("12000.00"),
            current_amount=Decimal("4800.00"),
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
        required_amount=Decimal("400.00"),
        allocated_amount=Decimal("300.00"),
    )

    assert allocation.goal_id == 1
    assert allocation.required_amount == Decimal("400.00")
    assert allocation.allocated_amount == Decimal("300.00")
    assert allocation.shortfall == Decimal("100.00")
    assert allocation.surplus == Decimal("0.00")
    assert allocation.is_fully_funded is False


def test_goal_allocation_normalizes_name():
    allocation = GoalAllocation(
        goal_id=1,
        goal_name="  Emergency Fund  ",
        priority=GoalPriority.HIGH,
        required_amount=Decimal("400.00"),
        allocated_amount=Decimal("400.00"),
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
            required_amount=Decimal("400.00"),
            allocated_amount=Decimal("400.00"),
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
            required_amount=Decimal("400.00"),
            allocated_amount=Decimal("400.00"),
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
            required_amount=Decimal("-1.00"),
            allocated_amount=Decimal("0.00"),
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
            required_amount=Decimal("400.00"),
            allocated_amount=Decimal("-1.00"),
        )


def test_goal_allocation_identifies_fully_funded_goal():
    allocation = GoalAllocation(
        goal_id=1,
        goal_name="Emergency Fund",
        priority=GoalPriority.HIGH,
        required_amount=Decimal("400.00"),
        allocated_amount=Decimal("400.00"),
    )

    assert allocation.shortfall == Decimal("0.00")
    assert allocation.is_fully_funded is True


def test_goal_allocation_calculates_surplus():
    allocation = GoalAllocation(
        goal_id=1,
        goal_name="Emergency Fund",
        priority=GoalPriority.HIGH,
        required_amount=Decimal("400.00"),
        allocated_amount=Decimal("450.00"),
    )

    assert allocation.shortfall == Decimal("0.00")
    assert allocation.surplus == Decimal("50.00")
    assert allocation.is_fully_funded is True


def test_goal_allocation_to_dict():
    allocation = GoalAllocation(
        goal_id=1,
        goal_name="Emergency Fund",
        priority=GoalPriority.CRITICAL,
        required_amount=Decimal("400.00"),
        allocated_amount=Decimal("300.00"),
    )

    result = allocation.to_dict()

    assert result == {
        "goal_id": 1,
        "goal_name": "Emergency Fund",
        "priority": "CRITICAL",
        "required_amount": "400.00",
        "allocated_amount": "300.00",
        "shortfall": "100.00",
        "surplus": "0.00",
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
        target_amount=Decimal("6000.00"),
        current_amount=Decimal("0.00"),
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
        target_amount=Decimal("6000.00"),
        current_amount=Decimal("0.00"),
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
        target_amount=Decimal("2400.00"),
        current_amount=Decimal("0.00"),
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
        target_amount=Decimal("6000.00"),
        current_amount=Decimal("0.00"),
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
        total_available=Decimal("700.00"),
    )

    emergency = plan.get_allocation_by_goal_id(1)
    car = plan.get_allocation_by_goal_id(3)
    vacation = plan.get_allocation_by_goal_id(2)

    assert emergency is not None
    assert car is not None
    assert vacation is not None

    assert emergency.required_amount == Decimal("400.00")
    assert emergency.allocated_amount == Decimal("400.00")

    assert car.required_amount == Decimal("600.00")
    assert car.allocated_amount == Decimal("300.00")

    assert vacation.required_amount == Decimal("300.00")
    assert vacation.allocated_amount == Decimal("0.00")


def test_allocate_goal_funding_when_all_goals_can_be_funded():
    plan = allocate_goal_funding(
        build_standard_requests(),
        total_available=Decimal("1500.00"),
    )

    assert plan.total_required == Decimal("1300.00")
    assert plan.total_allocated == Decimal("1300.00")
    assert plan.total_shortfall == Decimal("0.00")
    assert plan.remaining_cash == Decimal("200.00")
    assert plan.all_goals_funded is True


def test_allocate_goal_funding_with_partial_funding():
    plan = allocate_goal_funding(
        build_standard_requests(),
        total_available=Decimal("1000.00"),
    )

    assert plan.total_required == Decimal("1300.00")
    assert plan.total_allocated == Decimal("1000.00")
    assert plan.total_shortfall == Decimal("300.00")
    assert plan.remaining_cash == Decimal("0.00")
    assert plan.all_goals_funded is False


def test_allocate_goal_funding_with_no_available_cash():
    plan = allocate_goal_funding(
        build_standard_requests(),
        total_available=Decimal("0.00"),
    )

    assert plan.total_allocated == Decimal("0.00")
    assert plan.total_shortfall == Decimal("1300.00")
    assert plan.remaining_cash == Decimal("0.00")
    assert plan.all_goals_funded is False


def test_allocate_goal_funding_with_no_requests():
    plan = allocate_goal_funding(
        [],
        total_available=Decimal("1000.00"),
    )

    assert plan.allocations == []
    assert plan.total_required == Decimal("0.00")
    assert plan.total_allocated == Decimal("0.00")
    assert plan.total_shortfall == Decimal("0.00")
    assert plan.remaining_cash == Decimal("1000.00")
    assert plan.all_goals_funded is True


def test_allocate_goal_funding_does_not_modify_requests():
    requests = build_standard_requests()
    original_ids = [request.projection.goal_id for request in requests]

    allocate_goal_funding(
        requests,
        total_available=Decimal("700.00"),
    )

    assert [request.projection.goal_id for request in requests] == original_ids


def test_allocate_goal_funding_rejects_negative_total():
    with pytest.raises(
        ValueError,
        match="available",
    ):
        allocate_goal_funding(
            build_standard_requests(),
            total_available=Decimal("-1.00"),
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
            total_available=Decimal("1000.00"),
        )


def test_goal_allocation_plan_returns_defensive_copy():
    plan = allocate_goal_funding(
        build_standard_requests(),
        total_available=Decimal("1000.00"),
    )

    returned_allocations = plan.allocations
    returned_allocations.clear()

    assert len(plan.allocations) == 3


def test_goal_allocation_plan_rejects_duplicate_goal_ids():
    allocation = GoalAllocation(
        goal_id=1,
        goal_name="Emergency Fund",
        priority=GoalPriority.HIGH,
        required_amount=Decimal("400.00"),
        allocated_amount=Decimal("400.00"),
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
            total_available=Decimal("1000.00"),
        )


def test_goal_allocation_plan_to_dict():
    plan = allocate_goal_funding(
        build_standard_requests(),
        total_available=Decimal("1500.00"),
    )

    result = plan.to_dict()

    assert len(result["allocations"]) == 3
    assert result["total_available"] == "1500.00"
    assert result["total_required"] == "1300.00"
    assert result["total_allocated"] == "1300.00"
    assert result["total_shortfall"] == "0.00"
    assert result["remaining_cash"] == "200.00"
    assert result["all_goals_funded"] is True
