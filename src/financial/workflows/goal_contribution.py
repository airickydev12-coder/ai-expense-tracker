from src.financial.goals.models import Goal


def apply_contribution_to_goal(
    goal: Goal,
    contribution: float,
) -> Goal:
    """Apply a contribution to a financial goal."""
    if contribution < 0:
        raise ValueError("Goal contribution cannot be negative.")

    goal.current_amount += contribution

    if goal.current_amount > goal.target_amount:
        goal.current_amount = goal.target_amount

    return goal