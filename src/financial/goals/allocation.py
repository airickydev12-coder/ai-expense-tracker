from dataclasses import dataclass
from enum import IntEnum
from typing import Any

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
    required_amount: float
    allocated_amount: float

    def __post_init__(self) -> None:
        """Validate and normalize allocation data."""
        normalized_name = self.goal_name.strip()

        if self.goal_id <= 0:
            raise ValueError("Goal allocation ID must be greater than zero.")

        if not normalized_name:
            raise ValueError("Goal allocation name cannot be empty.")

        if self.required_amount < 0:
            raise ValueError("Goal required amount cannot be negative.")

        if self.allocated_amount < 0:
            raise ValueError("Goal allocated amount cannot be negative.")

        object.__setattr__(
            self,
            "goal_name",
            normalized_name,
        )

    @property
    def shortfall(self) -> float:
        """Return the amount still required for this funding period."""
        return max(
            self.required_amount - self.allocated_amount,
            0.0,
        )

    @property
    def surplus(self) -> float:
        """Return any amount allocated above the requirement."""
        return max(
            self.allocated_amount - self.required_amount,
            0.0,
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
            "required_amount": self.required_amount,
            "allocated_amount": self.allocated_amount,
            "shortfall": self.shortfall,
            "surplus": self.surplus,
            "is_fully_funded": self.is_fully_funded,
        }


class GoalAllocationPlan:
    """Represents a complete monthly goal-allocation plan."""

    def __init__(
        self,
        *,
        allocations: list[GoalAllocation],
        total_available: float,
    ) -> None:
        """Create and validate an allocation plan."""
        if total_available < 0:
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
    def total_available(self) -> float:
        """Return the total amount available for allocation."""
        return self._total_available

    @property
    def total_required(self) -> float:
        """Return the combined monthly funding requirement."""
        return sum(allocation.required_amount for allocation in self._allocations)

    @property
    def total_allocated(self) -> float:
        """Return the total amount allocated to goals."""
        return sum(allocation.allocated_amount for allocation in self._allocations)

    @property
    def total_shortfall(self) -> float:
        """Return the combined funding shortfall."""
        return sum(allocation.shortfall for allocation in self._allocations)

    @property
    def remaining_cash(self) -> float:
        """Return available cash remaining after allocation."""
        return max(
            self.total_available - self.total_allocated,
            0.0,
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
            "total_available": self.total_available,
            "total_required": self.total_required,
            "total_allocated": self.total_allocated,
            "total_shortfall": self.total_shortfall,
            "remaining_cash": self.remaining_cash,
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
    total_available: float,
) -> GoalAllocationPlan:
    """
    Allocate available monthly funding across financial goals.

    Higher-priority goals receive funding first. Goals with the
    same priority are ordered by target date and required amount.
    Allocations never exceed a goal's monthly requirement.
    """
    if total_available < 0:
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
