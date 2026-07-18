from dataclasses import dataclass
from datetime import date
from typing import Any

from src.financial.goals.allocation import (
    GoalAllocationPlan,
    GoalFundingRequest,
    GoalPriority,
    allocate_goal_funding,
)
from src.financial.goals.feasibility import (
    assess_goal_feasibility,
)
from src.financial.goals.models import Goal
from src.financial.goals.planning_models import (
    GoalFeasibilityAssessment,
    GoalFeasibilityStatus,
    GoalProjection,
)
from src.financial.goals.projections import (
    build_goal_projection,
)


@dataclass(frozen=True)
class GoalPlanningRequest:
    """Contains the planning information required for one goal."""

    goal: Goal
    target_date: date
    planned_monthly_contribution: float
    priority: GoalPriority = GoalPriority.MEDIUM

    def __post_init__(self) -> None:
        """Validate the goal-planning request."""
        if self.planned_monthly_contribution < 0:
            raise ValueError("Planned monthly contribution cannot be negative.")

        if not isinstance(self.priority, GoalPriority):
            raise TypeError("Goal planning priority must be a GoalPriority.")

    def to_dict(self) -> dict[str, Any]:
        """Convert the request to a dictionary."""
        return {
            "goal": self.goal.to_dict(),
            "target_date": self.target_date.isoformat(),
            "planned_monthly_contribution": (self.planned_monthly_contribution),
            "priority": self.priority.name,
        }


class GoalPlanningResult:
    """Represents a complete analysis of multiple financial goals."""

    def __init__(
        self,
        *,
        projections: list[GoalProjection],
        assessments: list[GoalFeasibilityAssessment],
        allocation_plan: GoalAllocationPlan,
    ) -> None:
        """Create and validate a goal-planning result."""
        projection_goal_ids = [projection.goal_id for projection in projections]

        assessment_goal_ids = [
            assessment.projection.goal_id for assessment in assessments
        ]

        allocation_goal_ids = [
            allocation.goal_id for allocation in allocation_plan.allocations
        ]

        if len(projection_goal_ids) != len(set(projection_goal_ids)):
            raise ValueError(
                "Goal planning result cannot contain duplicate " "projection goal IDs."
            )

        if len(assessment_goal_ids) != len(set(assessment_goal_ids)):
            raise ValueError(
                "Goal planning result cannot contain duplicate " "assessment goal IDs."
            )

        if set(projection_goal_ids) != set(assessment_goal_ids):
            raise ValueError(
                "Goal planning projections and assessments must "
                "contain the same goal IDs."
            )

        if set(projection_goal_ids) != set(allocation_goal_ids):
            raise ValueError(
                "Goal planning projections and allocations must "
                "contain the same goal IDs."
            )

        self._projections = tuple(projections)
        self._assessments = tuple(assessments)
        self._allocation_plan = allocation_plan

    @property
    def projections(self) -> list[GoalProjection]:
        """Return a defensive copy of the goal projections."""
        return list(self._projections)

    @property
    def assessments(
        self,
    ) -> list[GoalFeasibilityAssessment]:
        """Return a defensive copy of feasibility assessments."""
        return list(self._assessments)

    @property
    def allocation_plan(self) -> GoalAllocationPlan:
        """Return the monthly allocation plan."""
        return self._allocation_plan

    @property
    def total_goals(self) -> int:
        """Return the total number of analyzed goals."""
        return len(self._projections)

    @property
    def completed_goals(self) -> int:
        """Return the number of completed goals."""
        return self._count_status(GoalFeasibilityStatus.COMPLETED)

    @property
    def feasible_goals(self) -> int:
        """Return the number of incomplete but feasible goals."""
        return self._count_status(GoalFeasibilityStatus.FEASIBLE)

    @property
    def at_risk_goals(self) -> int:
        """Return the number of goals classified as at risk."""
        return self._count_status(GoalFeasibilityStatus.AT_RISK)

    @property
    def unfunded_goals(self) -> int:
        """Return the number of goals without planned funding."""
        return self._count_status(GoalFeasibilityStatus.UNFUNDED)

    @property
    def missed_deadline_goals(self) -> int:
        """Return the number of goals with missed deadlines."""
        return self._count_status(GoalFeasibilityStatus.MISSED_DEADLINE)

    @property
    def total_monthly_required(self) -> float:
        """Return the combined required monthly funding."""
        return self._allocation_plan.total_required

    @property
    def total_monthly_allocated(self) -> float:
        """Return the combined allocated monthly funding."""
        return self._allocation_plan.total_allocated

    @property
    def overall_funding_gap(self) -> float:
        """Return the combined monthly funding shortfall."""
        return self._allocation_plan.total_shortfall

    @property
    def remaining_monthly_cash(self) -> float:
        """Return unallocated monthly cash."""
        return self._allocation_plan.remaining_cash

    @property
    def all_goals_feasible(self) -> bool:
        """Return whether every goal is feasible or completed."""
        return all(assessment.is_feasible for assessment in self._assessments)

    def get_projection_by_goal_id(
        self,
        goal_id: int,
    ) -> GoalProjection | None:
        """Return a projection by goal ID."""
        for projection in self._projections:
            if projection.goal_id == goal_id:
                return projection

        return None

    def get_assessment_by_goal_id(
        self,
        goal_id: int,
    ) -> GoalFeasibilityAssessment | None:
        """Return a feasibility assessment by goal ID."""
        for assessment in self._assessments:
            if assessment.projection.goal_id == goal_id:
                return assessment

        return None

    def _count_status(
        self,
        status: GoalFeasibilityStatus,
    ) -> int:
        """Return the number of assessments with a status."""
        return sum(assessment.status == status for assessment in self._assessments)

    def to_dict(self) -> dict[str, Any]:
        """Convert the complete planning result to a dictionary."""
        return {
            "projections": [projection.to_dict() for projection in self._projections],
            "assessments": [assessment.to_dict() for assessment in self._assessments],
            "allocation_plan": (self._allocation_plan.to_dict()),
            "summary": {
                "total_goals": self.total_goals,
                "completed_goals": self.completed_goals,
                "feasible_goals": self.feasible_goals,
                "at_risk_goals": self.at_risk_goals,
                "unfunded_goals": self.unfunded_goals,
                "missed_deadline_goals": (self.missed_deadline_goals),
                "total_monthly_required": (self.total_monthly_required),
                "total_monthly_allocated": (self.total_monthly_allocated),
                "overall_funding_gap": (self.overall_funding_gap),
                "remaining_monthly_cash": (self.remaining_monthly_cash),
                "all_goals_feasible": (self.all_goals_feasible),
            },
        }


def build_projection(
    request: GoalPlanningRequest,
    *,
    as_of_date: date | None = None,
) -> GoalProjection:
    """Build a projection from a goal-planning request."""
    return build_goal_projection(
        request.goal,
        target_date=request.target_date,
        planned_monthly_contribution=(request.planned_monthly_contribution),
        as_of_date=as_of_date,
    )


def assess_goal(
    request: GoalPlanningRequest,
    *,
    as_of_date: date | None = None,
) -> GoalFeasibilityAssessment:
    """Build and assess a projection for one financial goal."""
    projection = build_projection(
        request,
        as_of_date=as_of_date,
    )

    return assess_goal_feasibility(projection)


def allocate_monthly_funding(
    requests: list[GoalPlanningRequest],
    *,
    total_available: float,
    as_of_date: date | None = None,
) -> GoalAllocationPlan:
    """Build projections and allocate monthly funding."""
    _validate_unique_goal_ids(requests)

    funding_requests = [
        GoalFundingRequest(
            projection=build_projection(
                request,
                as_of_date=as_of_date,
            ),
            priority=request.priority,
        )
        for request in requests
    ]

    return allocate_goal_funding(
        funding_requests,
        total_available=total_available,
    )


def analyze_goals(
    requests: list[GoalPlanningRequest],
    *,
    total_available: float,
    as_of_date: date | None = None,
) -> GoalPlanningResult:
    """
    Analyze projections, feasibility, and funding allocations.

    This is the primary application-facing entry point for the
    financial-goal planning feature.
    """
    if total_available < 0:
        raise ValueError("Total available funding cannot be negative.")

    _validate_unique_goal_ids(requests)

    projections = [
        build_projection(
            request,
            as_of_date=as_of_date,
        )
        for request in requests
    ]

    assessments = [assess_goal_feasibility(projection) for projection in projections]

    funding_requests = [
        GoalFundingRequest(
            projection=projection,
            priority=request.priority,
        )
        for request, projection in zip(
            requests,
            projections,
            strict=True,
        )
    ]

    allocation_plan = allocate_goal_funding(
        funding_requests,
        total_available=total_available,
    )

    return GoalPlanningResult(
        projections=projections,
        assessments=assessments,
        allocation_plan=allocation_plan,
    )


def _validate_unique_goal_ids(
    requests: list[GoalPlanningRequest],
) -> None:
    """Validate that each request represents a unique goal."""
    goal_ids = [request.goal.id for request in requests]

    if len(goal_ids) != len(set(goal_ids)):
        raise ValueError("Goal planning requests cannot contain duplicate " "goal IDs.")
