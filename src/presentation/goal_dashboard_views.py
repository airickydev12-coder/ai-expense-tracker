"""Presentation functions for financial-goal dashboards."""

from src.financial.application.goal_dashboard_service import (
    GoalDashboard,
    GoalDashboardItem,
)
from src.presentation.goal_planning_views import (
    format_currency,
    format_priority,
)


def render_goal_dashboard_item(
    item: GoalDashboardItem,
) -> str:
    """Render one compact goal-dashboard row."""
    priority = (
        format_priority(item.priority)
        if item.priority is not None
        else "Not assigned"
    )

    return (
        f"{item.goal_id}. {item.goal_name} | "
        f"{format_currency(item.current_amount)} of "
        f"{format_currency(item.target_amount)} | "
        f"{item.funding_percentage:.1f}% | "
        f"{item.status.value} | "
        f"Priority: {priority}"
    )


def render_goal_dashboard(
    dashboard: GoalDashboard,
) -> str:
    """Render a complete financial-goal dashboard."""
    lines = [
        "FINANCIAL GOAL DASHBOARD",
        "=" * 24,
        f"Total Goals: {dashboard.total_goals}",
        (
            "Total Target Amount: "
            f"{format_currency(dashboard.total_target_amount)}"
        ),
        (
            "Total Currently Saved: "
            f"{format_currency(dashboard.total_current_amount)}"
        ),
        (
            "Total Remaining Amount: "
            f"{format_currency(dashboard.total_remaining_amount)}"
        ),
        (
            "Overall Funding: "
            f"{dashboard.overall_funding_percentage:.1f}%"
        ),
        f"Completed Goals: {dashboard.completed_goals}",
        f"On-Track Goals: {dashboard.on_track_goals}",
        f"At-Risk Goals: {dashboard.at_risk_goals}",
        f"Unfunded Goals: {dashboard.unfunded_goals}",
        f"Missed Deadlines: {dashboard.missed_deadline_goals}",
        (
            "Planning Required: "
            f"{dashboard.planning_required_goals}"
        ),
    ]

    if dashboard.highest_priority_goal is None:
        lines.append("Highest-Priority Goal: Not assigned")
    else:
        highest = dashboard.highest_priority_goal
        lines.append(
            "Highest-Priority Goal: "
            f"{highest.goal_name} "
            f"({format_priority(highest.priority)})"
        )

    lines.extend(
        [
            "",
            "GOAL STATUS",
            "-" * 20,
        ]
    )

    if not dashboard.items:
        lines.append("No financial goals are available.")
    else:
        lines.extend(
            render_goal_dashboard_item(item)
            for item in dashboard.items
        )

    return "\n".join(lines)
