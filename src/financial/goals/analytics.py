"""Analytics helpers for financial goals."""

from decimal import Decimal

from src.core.money import ZERO
from src.financial.goals.models import Goal


def get_goal_progress_percentage(
    goal: Goal,
) -> float:
    """
    Return the goal completion percentage.

    Monetary arithmetic remains Decimal. The final percentage
    is converted to float for reporting and chart compatibility.
    """
    if goal.target_amount <= ZERO:
        return 0.0

    percentage = goal.current_amount / goal.target_amount * Decimal("100")

    return float(percentage)


def get_remaining_goal_amount(
    goal: Goal,
) -> Decimal:
    """Return the remaining amount needed to fund a goal."""
    remaining_amount = goal.target_amount - goal.current_amount

    return max(
        remaining_amount,
        ZERO,
    )


def is_goal_complete(
    goal: Goal,
) -> bool:
    """Return whether the goal is fully funded."""
    return goal.current_amount >= goal.target_amount


def get_total_goal_targets(
    goals: list[Goal],
) -> Decimal:
    """Return the combined target amount."""
    return sum(
        (goal.target_amount for goal in goals),
        ZERO,
    )


def get_total_goal_progress(
    goals: list[Goal],
) -> Decimal:
    """Return the combined funded amount."""
    return sum(
        (goal.current_amount for goal in goals),
        ZERO,
    )
