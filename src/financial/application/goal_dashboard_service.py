"""Application service for financial-goal dashboard summaries."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Mapping, Sequence

from src.core.exceptions import ValidationError
from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
    assess_goal,
)
from src.financial.goals.allocation import GoalPriority
from src.financial.goals.models import Goal
from src.financial.goals.planning_models import GoalFeasibilityStatus


ZERO_MONEY = Decimal("0.00")


class GoalDashboardStatus(Enum):
    """Dashboard status for one financial goal."""

    COMPLETED = "Completed"
    ON_TRACK = "On Track"
    AT_RISK = "At Risk"
    UNFUNDED = "Unfunded"
    MISSED_DEADLINE = "Missed Deadline"
    PLANNING_REQUIRED = "Planning Required"


@dataclass(frozen=True)
class GoalDashboardItem:
    """Dashboard information for one financial goal."""

    goal_id: int
    goal_name: str
    target_amount: Decimal
    current_amount: Decimal
    remaining_amount: Decimal
    funding_percentage: float
    status: GoalDashboardStatus
    priority: GoalPriority | None

    @property
    def is_complete(self) -> bool:
        """Return whether the goal is fully funded."""
        return self.status == GoalDashboardStatus.COMPLETED


@dataclass(frozen=True)
class GoalDashboard:
    """Aggregate dashboard information for all financial goals."""

    items: tuple[GoalDashboardItem, ...]
    total_target_amount: Decimal
    total_current_amount: Decimal
    total_remaining_amount: Decimal
    overall_funding_percentage: float
    completed_goals: int
    on_track_goals: int
    at_risk_goals: int
    unfunded_goals: int
    missed_deadline_goals: int
    planning_required_goals: int
    highest_priority_goal: GoalDashboardItem | None

    @property
    def total_goals(self) -> int:
        """Return the number of goals represented by the dashboard."""
        return len(self.items)


_PRIORITY_RANK = {
    GoalPriority.CRITICAL: 4,
    GoalPriority.HIGH: 3,
    GoalPriority.MEDIUM: 2,
    GoalPriority.LOW: 1,
}


def build_goal_dashboard(
    goals: Sequence[Goal],
    *,
    requests_by_goal_id: Mapping[int, GoalPlanningRequest] | None = None,
    as_of_date: date | None = None,
) -> GoalDashboard:
    """Build a dashboard from saved goals and optional planning requests."""
    planning_date = as_of_date or date.today()
    request_map = requests_by_goal_id or {}

    _validate_goals(goals)
    _validate_requests(request_map)

    items = tuple(
        _build_dashboard_item(
            goal,
            request=request_map.get(goal.id),
            as_of_date=planning_date,
        )
        for goal in goals
    )

    total_target_amount = sum(
        (item.target_amount for item in items),
        ZERO_MONEY,
    )
    total_current_amount = sum(
        (item.current_amount for item in items),
        ZERO_MONEY,
    )
    total_remaining_amount = sum(
        (item.remaining_amount for item in items),
        ZERO_MONEY,
    )

    overall_funding_percentage = _calculate_percentage(
        total_current_amount,
        total_target_amount,
    )

    highest_priority_goal = _select_highest_priority_goal(items)

    return GoalDashboard(
        items=items,
        total_target_amount=total_target_amount,
        total_current_amount=total_current_amount,
        total_remaining_amount=total_remaining_amount,
        overall_funding_percentage=overall_funding_percentage,
        completed_goals=_count_status(
            items,
            GoalDashboardStatus.COMPLETED,
        ),
        on_track_goals=_count_status(
            items,
            GoalDashboardStatus.ON_TRACK,
        ),
        at_risk_goals=_count_status(
            items,
            GoalDashboardStatus.AT_RISK,
        ),
        unfunded_goals=_count_status(
            items,
            GoalDashboardStatus.UNFUNDED,
        ),
        missed_deadline_goals=_count_status(
            items,
            GoalDashboardStatus.MISSED_DEADLINE,
        ),
        planning_required_goals=_count_status(
            items,
            GoalDashboardStatus.PLANNING_REQUIRED,
        ),
        highest_priority_goal=highest_priority_goal,
    )


def _build_dashboard_item(
    goal: Goal,
    *,
    request: GoalPlanningRequest | None,
    as_of_date: date,
) -> GoalDashboardItem:
    """Build one dashboard item."""
    remaining_amount = max(
        goal.target_amount - goal.current_amount,
        ZERO_MONEY,
    )

    funding_percentage = _calculate_percentage(
        goal.current_amount,
        goal.target_amount,
    )

    status = _resolve_status(
        goal,
        request=request,
        as_of_date=as_of_date,
    )

    return GoalDashboardItem(
        goal_id=goal.id,
        goal_name=goal.name,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        remaining_amount=remaining_amount,
        funding_percentage=funding_percentage,
        status=status,
        priority=(request.priority if request is not None else None),
    )


def _resolve_status(
    goal: Goal,
    *,
    request: GoalPlanningRequest | None,
    as_of_date: date,
) -> GoalDashboardStatus:
    """Resolve the dashboard status for one goal."""
    if goal.current_amount >= goal.target_amount:
        return GoalDashboardStatus.COMPLETED

    if request is None:
        return GoalDashboardStatus.PLANNING_REQUIRED

    assessment = assess_goal(
        request,
        as_of_date=as_of_date,
    )

    status_map = {
        GoalFeasibilityStatus.COMPLETED: (GoalDashboardStatus.COMPLETED),
        GoalFeasibilityStatus.FEASIBLE: (GoalDashboardStatus.ON_TRACK),
        GoalFeasibilityStatus.AT_RISK: (GoalDashboardStatus.AT_RISK),
        GoalFeasibilityStatus.UNFUNDED: (GoalDashboardStatus.UNFUNDED),
        GoalFeasibilityStatus.MISSED_DEADLINE: (GoalDashboardStatus.MISSED_DEADLINE),
    }

    return status_map[assessment.status]


def _priority_rank(
    item: GoalDashboardItem,
) -> int:
    """Return the numeric rank for a dashboard item's priority."""
    assert item.priority is not None

    return _PRIORITY_RANK[item.priority]


def _select_highest_priority_goal(
    items: Sequence[GoalDashboardItem],
) -> GoalDashboardItem | None:
    """Return the highest-priority incomplete goal with a planning request."""
    candidates = [
        item for item in items if not item.is_complete and item.priority is not None
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda item: (
            _priority_rank(item),
            item.remaining_amount,
            -item.goal_id,
        ),
    )


def _calculate_percentage(
    current_amount: Decimal,
    target_amount: Decimal,
) -> float:
    """
    Calculate a funding percentage capped at 100 percent.

    Monetary arithmetic remains Decimal. The final analytical
    percentage is converted to float for dashboard compatibility.
    """
    if target_amount <= ZERO_MONEY:
        return 0.0

    percentage = current_amount / target_amount * Decimal("100")

    capped_percentage = min(
        percentage,
        Decimal("100"),
    )

    return float(capped_percentage)


def _count_status(
    items: Sequence[GoalDashboardItem],
    status: GoalDashboardStatus,
) -> int:
    """Count dashboard items with the supplied status."""
    return sum(item.status == status for item in items)


def _validate_goals(
    goals: Sequence[Goal],
) -> None:
    """Validate dashboard goals."""
    goal_ids: list[int] = []

    for goal in goals:
        if not isinstance(goal, Goal):
            raise TypeError("Every dashboard goal must be a Goal instance.")

        goal_ids.append(goal.id)

    if len(goal_ids) != len(set(goal_ids)):
        raise ValidationError("Goal dashboard cannot contain duplicate goal IDs.")


def _validate_requests(
    requests_by_goal_id: Mapping[
        int,
        GoalPlanningRequest,
    ],
) -> None:
    """Validate planning-request mappings."""
    for goal_id, request in requests_by_goal_id.items():
        if not isinstance(goal_id, int):
            raise TypeError("Goal planning request keys must be integers.")

        if not isinstance(
            request,
            GoalPlanningRequest,
        ):
            raise TypeError(
                "Every dashboard planning request must be "
                "a GoalPlanningRequest instance."
            )

        if request.goal.id != goal_id:
            raise ValidationError(
                "Goal planning request key must match " "the request goal ID."
            )
