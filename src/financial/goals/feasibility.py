"""Goal feasibility evaluation."""

from src.core.money import ZERO
from src.financial.goals.planning_models import (
    GoalFeasibilityAssessment,
    GoalFeasibilityStatus,
    GoalProjection,
)


def assess_goal_feasibility(
    projection: GoalProjection,
) -> GoalFeasibilityAssessment:
    """Assess whether a projected goal plan is feasible."""
    if projection.is_complete:
        return GoalFeasibilityAssessment(
            projection=projection,
            status=GoalFeasibilityStatus.COMPLETED,
            is_feasible=True,
            summary=f"{projection.goal_name} is fully funded.",
            recommendation=(
                "Maintain the completed balance or begin "
                "planning the next financial goal."
            ),
        )

    if projection.has_deadline_passed:
        return GoalFeasibilityAssessment(
            projection=projection,
            status=GoalFeasibilityStatus.MISSED_DEADLINE,
            is_feasible=False,
            summary=(
                f"{projection.goal_name} has an outstanding "
                f"balance of ${projection.remaining_amount:,.2f}, "
                "but its target date has passed."
            ),
            recommendation=(
                "Choose a new target date and calculate a "
                "revised monthly contribution."
            ),
        )

    if projection.planned_monthly_contribution == ZERO:
        return GoalFeasibilityAssessment(
            projection=projection,
            status=GoalFeasibilityStatus.UNFUNDED,
            is_feasible=False,
            summary=(
                f"{projection.goal_name} requires "
                f"${projection.required_monthly_contribution:,.2f} "
                "per month, but no monthly contribution is planned."
            ),
            recommendation=(
                "Assign a recurring monthly contribution or " "extend the target date."
            ),
        )

    if (
        projection.planned_monthly_contribution
        >= projection.required_monthly_contribution
    ):
        return GoalFeasibilityAssessment(
            projection=projection,
            status=GoalFeasibilityStatus.FEASIBLE,
            is_feasible=True,
            summary=(
                f"{projection.goal_name} is on track with a "
                f"planned contribution of "
                f"${projection.planned_monthly_contribution:,.2f} "
                "per month."
            ),
            recommendation=(
                "Maintain the planned contribution and review " "progress regularly."
            ),
        )

    return GoalFeasibilityAssessment(
        projection=projection,
        status=GoalFeasibilityStatus.AT_RISK,
        is_feasible=False,
        summary=(
            f"{projection.goal_name} is short by "
            f"${projection.monthly_shortfall:,.2f} per month "
            "under the current plan."
        ),
        recommendation=(
            f"Increase the monthly contribution to at least "
            f"${projection.required_monthly_contribution:,.2f} "
            "or extend the target date."
        ),
    )
