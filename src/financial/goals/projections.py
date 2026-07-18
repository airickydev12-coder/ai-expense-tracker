import calendar
import math
from datetime import date

from src.financial.goals.analytics import (
    get_remaining_goal_amount,
)
from src.financial.goals.models import Goal
from src.financial.goals.planning_models import (
    GoalProjection,
)


def calculate_months_remaining(
    as_of_date: date,
    target_date: date,
) -> int:
    """
    Calculate the number of monthly contribution periods remaining.

    A partial future month counts as one contribution period.
    """
    if target_date <= as_of_date:
        return 0

    month_difference = (
        (target_date.year - as_of_date.year) * 12 + target_date.month - as_of_date.month
    )

    if target_date.day > as_of_date.day:
        month_difference += 1

    return max(
        month_difference,
        1,
    )


def calculate_required_monthly_contribution(
    remaining_amount: float,
    months_remaining: int,
) -> float:
    """Calculate the monthly contribution required by a deadline."""
    if remaining_amount < 0:
        raise ValueError("Remaining goal amount cannot be negative.")

    if months_remaining < 0:
        raise ValueError("Months remaining cannot be negative.")

    if remaining_amount == 0:
        return 0.0

    if months_remaining == 0:
        return remaining_amount

    return remaining_amount / months_remaining


def add_months(
    starting_date: date,
    months: int,
) -> date:
    """Return a date advanced by a number of calendar months."""
    if months < 0:
        raise ValueError("Months to add cannot be negative.")

    target_month_index = starting_date.year * 12 + starting_date.month - 1 + months

    target_year = target_month_index // 12
    target_month = target_month_index % 12 + 1

    target_day = min(
        starting_date.day,
        calendar.monthrange(
            target_year,
            target_month,
        )[1],
    )

    return date(
        target_year,
        target_month,
        target_day,
    )


def calculate_projected_completion_date(
    *,
    as_of_date: date,
    remaining_amount: float,
    monthly_contribution: float,
) -> date | None:
    """Calculate the estimated completion date for a goal."""
    if remaining_amount < 0:
        raise ValueError("Remaining goal amount cannot be negative.")

    if monthly_contribution < 0:
        raise ValueError("Monthly contribution cannot be negative.")

    if remaining_amount == 0:
        return as_of_date

    if monthly_contribution == 0:
        return None

    months_needed = math.ceil(remaining_amount / monthly_contribution)

    return add_months(
        as_of_date,
        months_needed,
    )


def build_goal_projection(
    goal: Goal,
    *,
    target_date: date,
    planned_monthly_contribution: float,
    as_of_date: date | None = None,
) -> GoalProjection:
    """Build a financial projection for one goal."""
    if planned_monthly_contribution < 0:
        raise ValueError("Planned monthly contribution cannot be negative.")

    effective_as_of_date = as_of_date if as_of_date is not None else date.today()

    remaining_amount = get_remaining_goal_amount(goal)

    months_remaining = calculate_months_remaining(
        effective_as_of_date,
        target_date,
    )

    required_monthly_contribution = calculate_required_monthly_contribution(
        remaining_amount,
        months_remaining,
    )

    monthly_contribution_difference = (
        planned_monthly_contribution - required_monthly_contribution
    )

    projected_completion_date = calculate_projected_completion_date(
        as_of_date=effective_as_of_date,
        remaining_amount=remaining_amount,
        monthly_contribution=(planned_monthly_contribution),
    )

    return GoalProjection(
        goal_id=goal.id,
        goal_name=goal.name,
        as_of_date=effective_as_of_date,
        target_date=target_date,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        remaining_amount=remaining_amount,
        months_remaining=months_remaining,
        required_monthly_contribution=(required_monthly_contribution),
        planned_monthly_contribution=(planned_monthly_contribution),
        monthly_contribution_difference=(monthly_contribution_difference),
        projected_completion_date=(projected_completion_date),
    )
