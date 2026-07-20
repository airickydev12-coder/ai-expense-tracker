from datetime import date

from src.financial.application.goal_planning_service import (
    GoalPlanningRequest,
    GoalPlanningResult,
    MoneyInput,
    to_money,
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


def format_currency(amount: MoneyInput) -> str:
    """Format a monetary amount as United States currency."""
    normalized_amount = to_money(amount)
    return f"${normalized_amount:,.2f}"


def format_date(value: date | None) -> str:
    """Format a date for display."""
    if value is None:
        return "Not projected"
    return value.strftime("%B %d, %Y")


def format_priority(priority: GoalPriority) -> str:
    """Format a goal priority for display."""
    return priority.name.replace("_", " ").title()


def format_boolean(value: bool) -> str:
    """Format a boolean value for display."""
    return "Yes" if value else "No"


def render_goal_planning_request(request: GoalPlanningRequest) -> str:
    """Render one goal-planning request."""
    goal = request.goal
    lines = [
        f"Goal: {goal.name}",
        f"Goal ID: {goal.id}",
        f"Current Amount: {format_currency(goal.current_amount)}",
        f"Target Amount: {format_currency(goal.target_amount)}",
        f"Target Date: {format_date(request.target_date)}",
        (
            "Planned Monthly Contribution: "
            f"{format_currency(request.planned_monthly_contribution)}"
        ),
        f"Priority: {format_priority(request.priority)}",
    ]
    return "\n".join(lines)


def render_goal_projection(projection: GoalProjection) -> str:
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
        f"Current Amount: {format_currency(projection.current_amount)}",
        f"Target Amount: {format_currency(projection.target_amount)}",
        f"Remaining Amount: {format_currency(projection.remaining_amount)}",
        f"Target Date: {format_date(projection.target_date)}",
        f"Months Remaining: {projection.months_remaining}",
        (
            "Required Monthly Contribution: "
            f"{format_currency(projection.required_monthly_contribution)}"
        ),
        (
            "Planned Monthly Contribution: "
            f"{format_currency(projection.planned_monthly_contribution)}"
        ),
        (
            f"{contribution_difference_label}: "
            f"{format_currency(contribution_difference)}"
        ),
        (
            "Projected Completion Date: "
            f"{format_date(projection.projected_completion_date)}"
        ),
        f"Goal Complete: {format_boolean(projection.is_complete)}",
        f"Deadline Passed: {format_boolean(projection.has_deadline_passed)}",
    ]
    return "\n".join(lines)


def render_goal_feasibility_assessment(
    assessment: GoalFeasibilityAssessment,
) -> str:
    """Render one actionable goal-feasibility assessment."""
    projection = assessment.projection
    contribution_difference_label = (
        "Monthly Contribution Surplus"
        if projection.monthly_contribution_difference >= 0
        else "Monthly Contribution Shortfall"
    )
    contribution_difference = abs(projection.monthly_contribution_difference)
    lines = [
        f"Goal: {projection.goal_name}",
        f"Status: {assessment.status.value}",
        f"Feasible: {format_boolean(assessment.is_feasible)}",
        f"Remaining Amount: {format_currency(projection.remaining_amount)}",
        f"Months Remaining: {projection.months_remaining}",
        (
            "Required Monthly Contribution: "
            f"{format_currency(projection.required_monthly_contribution)}"
        ),
        (
            "Planned Monthly Contribution: "
            f"{format_currency(projection.planned_monthly_contribution)}"
        ),
        (
            f"{contribution_difference_label}: "
            f"{format_currency(contribution_difference)}"
        ),
        (
            "Projected Completion Date: "
            f"{format_date(projection.projected_completion_date)}"
        ),
        f"Summary: {assessment.summary}",
        f"Recommendation: {assessment.recommendation}",
    ]
    return "\n".join(lines)


def render_goal_allocation(allocation: GoalAllocation) -> str:
    """Render one monthly goal allocation."""
    lines = [
        f"Goal: {allocation.goal_name}",
        f"Goal ID: {allocation.goal_id}",
        f"Priority: {format_priority(allocation.priority)}",
        f"Required Amount: {format_currency(allocation.required_amount)}",
        f"Allocated Amount: {format_currency(allocation.allocated_amount)}",
        f"Shortfall: {format_currency(allocation.shortfall)}",
        f"Fully Funded: {format_boolean(allocation.is_fully_funded)}",
    ]
    return "\n".join(lines)


def render_goal_allocation_plan(plan: GoalAllocationPlan) -> str:
    """Render a complete monthly goal-allocation plan."""
    lines = [
        "MONTHLY GOAL FUNDING ALLOCATION",
        "=" * 31,
        "",
    ]
    if not plan.allocations:
        lines.append("No financial goals were provided for allocation.")
    else:
        for index, allocation in enumerate(plan.allocations, start=1):
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
            f"Total Available: {format_currency(plan.total_available)}",
            f"Total Required: {format_currency(plan.total_required)}",
            f"Total Allocated: {format_currency(plan.total_allocated)}",
            f"Total Shortfall: {format_currency(plan.total_shortfall)}",
            f"Remaining Cash: {format_currency(plan.remaining_cash)}",
            f"All Goals Funded: {format_boolean(plan.all_goals_funded)}",
        ]
    )
    return "\n".join(lines)


def render_goal_priority_report(result: GoalPlanningResult) -> str:
    """Render goals in recommended priority-based funding order."""
    allocations = result.allocation_plan.allocations
    lines = [
        "GOAL PRIORITIZATION REPORT",
        "=" * 26,
        "",
    ]
    if not allocations:
        lines.extend(
            [
                "No goals are available for prioritization.",
                (
                    "Recommendation: Create at least one financial goal "
                    "and assign a priority before building a funding order."
                ),
            ]
        )
        return "\n".join(lines)
    lines.extend(["RECOMMENDED FUNDING ORDER", "-" * 25, ""])
    for rank, allocation in enumerate(allocations, start=1):
        funding_status = (
            "Fully funded"
            if allocation.is_fully_funded
            else f"{format_currency(allocation.shortfall)} short"
        )
        lines.extend(
            [
                f"Rank {rank}",
                f"Goal: {allocation.goal_name}",
                f"Priority: {format_priority(allocation.priority)}",
                (
                    "Required Monthly Funding: "
                    f"{format_currency(allocation.required_amount)}"
                ),
                (
                    "Allocated Monthly Funding: "
                    f"{format_currency(allocation.allocated_amount)}"
                ),
                f"Funding Status: {funding_status}",
                "",
            ]
        )
    underfunded_allocations = [
        allocation for allocation in allocations if not allocation.is_fully_funded
    ]
    if underfunded_allocations:
        next_goal = underfunded_allocations[0]
        recommendation = (
            f"Direct the next {format_currency(next_goal.shortfall)} "
            f"of available monthly cash to {next_goal.goal_name} "
            "before increasing funding for lower-priority goals."
        )
    else:
        recommendation = (
            "Maintain the current allocation order because every goal "
            "is fully funded."
        )
    lines.extend(["RECOMMENDATION", "-" * 14, recommendation])
    return "\n".join(lines)


def render_goal_funding_gap_report(result: GoalPlanningResult) -> str:
    """Render the monthly funding gap across all financial goals."""
    plan = result.allocation_plan
    lines = [
        "MONTHLY FUNDING GAP REPORT",
        "=" * 26,
        f"Monthly Funding Required: {format_currency(plan.total_required)}",
        f"Monthly Funding Available: {format_currency(plan.total_available)}",
        f"Monthly Funding Gap: {format_currency(plan.total_shortfall)}",
    ]
    if not plan.allocations:
        lines.extend(
            [
                "Status: No goals available",
                (
                    "Recommendation: Create a financial goal before "
                    "evaluating monthly funding requirements."
                ),
            ]
        )
        return "\n".join(lines)
    if plan.all_goals_funded:
        lines.extend(
            [
                "Status: Fully funded",
                (
                    "Recommendation: Maintain the current monthly "
                    "funding level while reviewing goal progress regularly."
                ),
            ]
        )
        return "\n".join(lines)
    lines.extend(
        [
            "Status: Funding shortfall",
            "",
            "GOALS REQUIRING ADDITIONAL FUNDING",
            "-" * 34,
        ]
    )
    for allocation in plan.allocations:
        if allocation.is_fully_funded:
            continue
        lines.append(
            f"{allocation.goal_name} "
            f"({format_priority(allocation.priority)}): "
            f"{format_currency(allocation.shortfall)} short"
        )
    lines.extend(
        [
            "",
            (
                "Recommendation: Increase monthly goal funding by "
                f"{format_currency(plan.total_shortfall)} or revise "
                "goal amounts, deadlines, or priorities."
            ),
        ]
    )
    return "\n".join(lines)


def render_goal_planning_summary(result: GoalPlanningResult) -> str:
    """Render the summary for a complete goal-planning result."""
    lines = [
        "GOAL PLANNING SUMMARY",
        "=" * 21,
        f"Total Goals: {result.total_goals}",
        f"Completed Goals: {result.completed_goals}",
        f"Feasible Goals: {result.feasible_goals}",
        f"At-Risk Goals: {result.at_risk_goals}",
        f"Unfunded Goals: {result.unfunded_goals}",
        f"Missed Deadlines: {result.missed_deadline_goals}",
        f"Total Monthly Required: {format_currency(result.total_monthly_required)}",
        f"Total Monthly Allocated: {format_currency(result.total_monthly_allocated)}",
        f"Overall Funding Gap: {format_currency(result.overall_funding_gap)}",
        f"Remaining Monthly Cash: {format_currency(result.remaining_monthly_cash)}",
        f"All Goals Feasible: {format_boolean(result.all_goals_feasible)}",
    ]
    return "\n".join(lines)


def render_goal_planning_result(result: GoalPlanningResult) -> str:
    """Render a complete financial-goal planning report."""
    lines = [
        "FINANCIAL GOAL PLANNING REPORT",
        "=" * 30,
        "",
        render_goal_planning_summary(result),
        "",
        render_goal_priority_report(result),
        "",
        render_goal_funding_gap_report(result),
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
    lines.extend(["", "GOAL PROJECTIONS", "=" * 16, ""])
    for index, projection in enumerate(result.projections, start=1):
        lines.extend(
            [
                f"Projection {index}",
                "-" * 20,
                render_goal_projection(projection),
                "",
            ]
        )
    lines.extend(["FEASIBILITY ASSESSMENTS", "=" * 23, ""])
    for index, assessment in enumerate(result.assessments, start=1):
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
    lines = ["GOAL PLANNING REQUESTS", "=" * 22, ""]
    for index, request in enumerate(requests, start=1):
        lines.extend(
            [
                f"Request {index}",
                "-" * 20,
                render_goal_planning_request(request),
                "",
            ]
        )
    return "\n".join(lines).rstrip()
