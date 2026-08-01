from src.financial.goals.models import Goal
from decimal import Decimal


def apply_contribution_to_goal(
    goal: Goal,
    contribution: Decimal,
) -> Goal:
    """Apply a contribution to a financial goal."""
    if contribution < Decimal("0"):
        raise ValueError("Goal contribution cannot be negative.")

    goal.current_amount += contribution

    if goal.current_amount > goal.target_amount:
        goal.current_amount = goal.target_amount

    return goal
