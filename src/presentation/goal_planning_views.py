from datetime import date

from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
    GoalPlanningResult,
)
from src.financial.goals.allocation import (
    GoalAllocation,
    GoalAllocationPlan,
    GoalPriority,
)
from src.financial.goals.planning_models import (
    GoalFeasibilityAssessment,
    GoalProjection,
)


def format_currency(
    amount: float,
) -> str:
    """Format a numeric amount as United States currency."""
    return f"${amount:,.2f}"


def format_date(
    value: date | None,
) -> str:
    """Format a date for display."""
    if value is None:
        return "Not projected"

    return value.strftime("%B %d, %Y")


def format_priority(
    priority: GoalPriority,
) -> str:
    """Format a goal priority for display."""
    return priority.name.replace(
        "_",
        " ",
    ).title()


def format_boolean(
    value: bool,
) -> str:
    """Format a boolean value for display."""
    return "Yes" if value else "No"


def render_goal_planning_request(
    request: GoalPlanningRequest,
) -> str:
    """Render one goal-planning request."""
    goal = request.goal

    lines = [
        f"Goal: {goal.name}",
        f"Goal ID: {goal.id}",
        ("Current Amount: " f"{format_currency(goal.current_amount)}"),
        ("Target Amount: " f"{format_currency(goal.target_amount)}"),
        ("Target Date: " f"{format_date(request.target_date)}"),
        (
            "Planned Monthly Contribution: "
            f"{format_currency(request.planned_monthly_contribution)}"
        ),
        ("Priority: " f"{format_priority(request.priority)}"),
    ]

    return "\n".join(lines)


def render_goal_projection(
    projection: GoalProjection,
) -> str:
    """Render one financial-goal projection."""
    contribution_difference_label = (
        "Monthly Contribution Surplus"
        if projection.monthly_contribution_difference >= 0
        else "Monthly Contribution Shortfall"
    )

    contribution_difference = abs(projection.monthly_contribution_difference)

    lines = [
        f"Goal: {projection.goal_name}",
        f"Goal ID: {projection.goal_id}",
        ("Current Amount: " f"{format_currency(projection.current_amount)}"),
        ("Target Amount: " f"{format_currency(projection.target_amount)}"),
        ("Remaining Amount: " f"{format_currency(projection.remaining_amount)}"),
        ("Target Date: " f"{format_date(projection.target_date)}"),
        ("Months Remaining: " f"{projection.months_remaining}"),
        (
            "Required Monthly Contribution: "
            f"{format_currency(
                projection.required_monthly_contribution
            )}"
        ),
        (
            "Planned Monthly Contribution: "
            f"{format_currency(
                projection.planned_monthly_contribution
            )}"
        ),
        (
            f"{contribution_difference_label}: "
            f"{format_currency(contribution_difference)}"
        ),
        (
            "Projected Completion Date: "
            f"{format_date(
                projection.projected_completion_date
            )}"
        ),
        ("Goal Complete: " f"{format_boolean(projection.is_complete)}"),
        (
            "Deadline Passed: "
            f"{format_boolean(
                projection.has_deadline_passed
            )}"
        ),
    ]

    return "\n".join(lines)


def render_goal_feasibility_assessment(
    assessment: GoalFeasibilityAssessment,
) -> str:
    """Render one goal-feasibility assessment."""
    projection = assessment.projection

    lines = [
        f"Goal: {projection.goal_name}",
        f"Status: {assessment.status.value}",
        ("Feasible: " f"{format_boolean(assessment.is_feasible)}"),
        f"Summary: {assessment.summary}",
        ("Recommendation: " f"{assessment.recommendation}"),
    ]

    return "\n".join(lines)


def render_goal_allocation(
    allocation: GoalAllocation,
) -> str:
    """Render one monthly goal allocation."""
    lines = [
        f"Goal: {allocation.goal_name}",
        f"Goal ID: {allocation.goal_id}",
        ("Priority: " f"{format_priority(allocation.priority)}"),
        ("Required Amount: " f"{format_currency(allocation.required_amount)}"),
        ("Allocated Amount: " f"{format_currency(allocation.allocated_amount)}"),
        ("Shortfall: " f"{format_currency(allocation.shortfall)}"),
        ("Fully Funded: " f"{format_boolean(allocation.is_fully_funded)}"),
    ]

    return "\n".join(lines)


def render_goal_allocation_plan(
    plan: GoalAllocationPlan,
) -> str:
    """Render a complete monthly goal-allocation plan."""
    lines = [
        "MONTHLY GOAL FUNDING ALLOCATION",
        "=" * 31,
        "",
    ]

    if not plan.allocations:
        lines.append("No financial goals were provided for allocation.")
    else:
        for index, allocation in enumerate(
            plan.allocations,
            start=1,
        ):
            lines.extend(
                [
                    f"Allocation {index}",
                    "-" * 20,
                    render_goal_allocation(allocation),
                    "",
                ]
            )

    lines.extend(
        [
            "ALLOCATION SUMMARY",
            "-" * 20,
            ("Total Available: " f"{format_currency(plan.total_available)}"),
            ("Total Required: " f"{format_currency(plan.total_required)}"),
            ("Total Allocated: " f"{format_currency(plan.total_allocated)}"),
            ("Total Shortfall: " f"{format_currency(plan.total_shortfall)}"),
            ("Remaining Cash: " f"{format_currency(plan.remaining_cash)}"),
            ("All Goals Funded: " f"{format_boolean(plan.all_goals_funded)}"),
        ]
    )

    return "\n".join(lines)


def render_goal_planning_summary(
    result: GoalPlanningResult,
) -> str:
    """Render the summary for a complete goal-planning result."""
    lines = [
        "GOAL PLANNING SUMMARY",
        "=" * 21,
        ("Total Goals: " f"{result.total_goals}"),
        ("Completed Goals: " f"{result.completed_goals}"),
        ("Feasible Goals: " f"{result.feasible_goals}"),
        ("At-Risk Goals: " f"{result.at_risk_goals}"),
        ("Unfunded Goals: " f"{result.unfunded_goals}"),
        ("Missed Deadlines: " f"{result.missed_deadline_goals}"),
        (
            "Total Monthly Required: "
            f"{format_currency(
                result.total_monthly_required
            )}"
        ),
        (
            "Total Monthly Allocated: "
            f"{format_currency(
                result.total_monthly_allocated
            )}"
        ),
        (
            "Overall Funding Gap: "
            f"{format_currency(
                result.overall_funding_gap
            )}"
        ),
        (
            "Remaining Monthly Cash: "
            f"{format_currency(
                result.remaining_monthly_cash
            )}"
        ),
        (
            "All Goals Feasible: "
            f"{format_boolean(
                result.all_goals_feasible
            )}"
        ),
    ]

    return "\n".join(lines)


def render_goal_planning_result(
    result: GoalPlanningResult,
) -> str:
    """Render a complete financial-goal planning report."""
    lines = [
        "FINANCIAL GOAL PLANNING REPORT",
        "=" * 30,
        "",
        render_goal_planning_summary(result),
    ]

    if not result.projections:
        lines.extend(
            [
                "",
                "No financial goals are available for analysis.",
                "",
                render_goal_allocation_plan(result.allocation_plan),
            ]
        )

        return "\n".join(lines)

    lines.extend(
        [
            "",
            "GOAL PROJECTIONS",
            "=" * 16,
            "",
        ]
    )

    for index, projection in enumerate(
        result.projections,
        start=1,
    ):
        lines.extend(
            [
                f"Projection {index}",
                "-" * 20,
                render_goal_projection(projection),
                "",
            ]
        )

    lines.extend(
        [
            "FEASIBILITY ASSESSMENTS",
            "=" * 23,
            "",
        ]
    )

    for index, assessment in enumerate(
        result.assessments,
        start=1,
    ):
        lines.extend(
            [
                f"Assessment {index}",
                "-" * 20,
                render_goal_feasibility_assessment(assessment),
                "",
            ]
        )

    lines.append(render_goal_allocation_plan(result.allocation_plan))

    return "\n".join(lines)


def render_goal_planning_request_list(
    requests: list[GoalPlanningRequest],
) -> str:
    """Render a collection of goal-planning requests."""
    if not requests:
        return "No goal-planning requests are available."

    lines = [
        "GOAL PLANNING REQUESTS",
        "=" * 22,
        "",
    ]

    for index, request in enumerate(
        requests,
        start=1,
    ):
        lines.extend(
            [
                f"Request {index}",
                "-" * 20,
                render_goal_planning_request(request),
                "",
            ]
        )

    return "\n".join(lines).rstrip()
