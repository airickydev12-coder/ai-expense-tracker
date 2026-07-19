from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum
from typing import Any

from src.core.money import (
    ZERO,
    money_to_json,
    to_money,
)
from src.financial.goals.planning_models import (
    GoalProjection,
)


class GoalPriority(IntEnum):
    """Priority used when allocating money across goals."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class GoalFundingRequest:
    """Represents a goal requesting monthly funding."""

    projection: GoalProjection
    priority: GoalPriority = GoalPriority.MEDIUM

    def to_dict(self) -> dict[str, Any]:
        """Convert the funding request to a dictionary."""
        return {
            "projection": self.projection.to_dict(),
            "priority": self.priority.name,
        }


@dataclass(frozen=True)
class GoalAllocation:
    """Represents the monthly allocation assigned to one goal."""

    goal_id: int
    goal_name: str
    priority: GoalPriority
    required_amount: Decimal
    allocated_amount: Decimal

    def __post_init__(self) -> None:
        """Validate and normalize allocation data."""
        normalized_name = self.goal_name.strip()

        required_amount = to_money(self.required_amount)
        allocated_amount = to_money(self.allocated_amount)

        if self.goal_id <= 0:
            raise ValueError("Goal allocation ID must be greater than zero.")

        if not normalized_name:
            raise ValueError("Goal allocation name cannot be empty.")

        if required_amount < ZERO:
            raise ValueError("Goal required amount cannot be negative.")

        if allocated_amount < ZERO:
            raise ValueError("Goal allocated amount cannot be negative.")

        object.__setattr__(self, "goal_name", normalized_name)
        object.__setattr__(self, "required_amount", required_amount)
        object.__setattr__(self, "allocated_amount", allocated_amount)

    @property
    def shortfall(self) -> Decimal:
        """Return the amount still required for this funding period."""
        return max(
            self.required_amount - self.allocated_amount,
            ZERO,
        )

    @property
    def surplus(self) -> Decimal:
        """Return any amount allocated above the requirement."""
        return max(
            self.allocated_amount - self.required_amount,
            ZERO,
        )

    @property
    def is_fully_funded(self) -> bool:
        """Return whether the monthly requirement was fully funded."""
        return self.allocated_amount >= self.required_amount

    def to_dict(self) -> dict[str, Any]:
        """Convert the allocation to a dictionary."""
        return {
            "goal_id": self.goal_id,
            "goal_name": self.goal_name,
            "priority": self.priority.name,
            "required_amount": money_to_json(self.required_amount),
            "allocated_amount": money_to_json(self.allocated_amount),
            "shortfall": money_to_json(self.shortfall),
            "surplus": money_to_json(self.surplus),
            "is_fully_funded": self.is_fully_funded,
        }


class GoalAllocationPlan:
    """Represents a complete monthly goal-allocation plan."""

    def __init__(
        self,
        *,
        allocations: list[GoalAllocation],
        total_available: Decimal,
    ) -> None:
        """Create and validate an allocation plan."""
        total_available = to_money(total_available)

        if total_available < ZERO:
            raise ValueError("Total available funding cannot be negative.")

        goal_ids = [allocation.goal_id for allocation in allocations]

        if len(goal_ids) != len(set(goal_ids)):
            raise ValueError("Goal allocation plan cannot contain duplicate goal IDs.")

        self._allocations = tuple(allocations)
        self._total_available = total_available

    @property
    def allocations(self) -> list[GoalAllocation]:
        """Return a defensive copy of goal allocations."""
        return list(self._allocations)

    @property
    def total_available(self) -> Decimal:
        """Return the total amount available for allocation."""
        return self._total_available

    @property
    def total_required(self) -> Decimal:
        """Return the combined monthly funding requirement."""
        return sum(
            (allocation.required_amount for allocation in self._allocations),
            ZERO,
        )

    @property
    def total_allocated(self) -> Decimal:
        """Return the total amount allocated to goals."""
        return sum(
            (allocation.allocated_amount for allocation in self._allocations),
            ZERO,
        )

    @property
    def total_shortfall(self) -> Decimal:
        """Return the combined funding shortfall."""
        return sum(
            (allocation.shortfall for allocation in self._allocations),
            ZERO,
        )

    @property
    def remaining_cash(self) -> Decimal:
        """Return available cash remaining after allocation."""
        return max(
            self.total_available - self.total_allocated,
            ZERO,
        )

    @property
    def all_goals_funded(self) -> bool:
        """Return whether every monthly goal requirement was funded."""
        return all(allocation.is_fully_funded for allocation in self._allocations)

    def get_allocation_by_goal_id(
        self,
        goal_id: int,
    ) -> GoalAllocation | None:
        """Return an allocation by goal ID."""
        for allocation in self._allocations:
            if allocation.goal_id == goal_id:
                return allocation

        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert the allocation plan to a dictionary."""
        return {
            "allocations": [allocation.to_dict() for allocation in self._allocations],
            "total_available": money_to_json(self.total_available),
            "total_required": money_to_json(self.total_required),
            "total_allocated": money_to_json(self.total_allocated),
            "total_shortfall": money_to_json(self.total_shortfall),
            "remaining_cash": money_to_json(self.remaining_cash),
            "all_goals_funded": self.all_goals_funded,
        }


def prioritize_goal_funding_requests(
    requests: list[GoalFundingRequest],
) -> list[GoalFundingRequest]:
    """
    Return funding requests in allocation order.

    Requests are ranked by:

    1. Highest priority
    2. Earliest target date
    3. Largest required monthly contribution
    4. Lowest goal ID
    """
    return sorted(
        requests,
        key=lambda request: (
            -int(request.priority),
            request.projection.target_date,
            -request.projection.required_monthly_contribution,
            request.projection.goal_id,
        ),
    )


def allocate_goal_funding(
    requests: list[GoalFundingRequest],
    *,
    total_available: Decimal,
) -> GoalAllocationPlan:
    """
    Allocate available monthly funding across financial goals.
    """
    total_available = to_money(total_available)

    if total_available < ZERO:
        raise ValueError("Total available funding cannot be negative.")

    goal_ids = [request.projection.goal_id for request in requests]

    if len(goal_ids) != len(set(goal_ids)):
        raise ValueError("Funding requests cannot contain duplicate goal IDs.")

    prioritized_requests = prioritize_goal_funding_requests(requests)

    remaining_cash = total_available
    allocations: list[GoalAllocation] = []

    for request in prioritized_requests:
        required_amount = request.projection.required_monthly_contribution

        allocated_amount = min(
            required_amount,
            remaining_cash,
        )

        allocations.append(
            GoalAllocation(
                goal_id=request.projection.goal_id,
                goal_name=request.projection.goal_name,
                priority=request.priority,
                required_amount=required_amount,
                allocated_amount=allocated_amount,
            )
        )

        remaining_cash -= allocated_amount

    return GoalAllocationPlan(
        allocations=allocations,
        total_available=total_available,
    )
