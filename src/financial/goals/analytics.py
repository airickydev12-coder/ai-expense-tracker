from src.financial.goals.models import Goal


def get_goal_progress_percentage(
    goal: Goal,
) -> float:
    """Return goal completion percentage."""
    if goal.target_amount <= 0:
        return 0.0

    return (
        goal.current_amount
        / goal.target_amount
    ) * 100


def get_remaining_goal_amount(
    goal: Goal,
) -> float:
    """Return the remaining amount needed."""
    return max(
        goal.target_amount - goal.current_amount,
        0.0,
    )


def is_goal_complete(
    goal: Goal,
) -> bool:
    """Return whether the goal is fully funded."""
    return goal.current_amount >= goal.target_amount


def get_total_goal_targets(
    goals: list[Goal],
) -> float:
    """Return the combined target amount."""
    return sum(
        goal.target_amount
        for goal in goals
    )


def get_total_goal_progress(
    goals: list[Goal],
) -> float:
    """Return the combined funded amount."""
    return sum(
        goal.current_amount
        for goal in goals
    )