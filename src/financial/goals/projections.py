"""Projection calculations for financial goals."""

import calendar
import math
from datetime import date
from decimal import Decimal
from typing import TypeAlias

from src.core.exceptions import ValidationError
from src.core.money import (
    ZERO,
    subtract_money,
    to_money,
)
from src.financial.goals.analytics import (
    get_remaining_goal_amount,
)
from src.financial.goals.models import Goal
from src.financial.goals.planning_models import (
    GoalProjection,
)


MoneyInput: TypeAlias = Decimal | int | float | str


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
    remaining_amount: MoneyInput,
    months_remaining: int,
) -> Decimal:
    """Calculate the monthly contribution required by a deadline."""
    normalized_remaining = to_money(remaining_amount)

    if normalized_remaining < ZERO:
        raise ValidationError("Remaining goal amount cannot be negative.")

    if months_remaining < 0:
        raise ValidationError("Months remaining cannot be negative.")

    if normalized_remaining == ZERO:
        return ZERO

    if months_remaining == 0:
        return normalized_remaining

    return to_money(normalized_remaining / Decimal(months_remaining))


def add_months(
    starting_date: date,
    months: int,
) -> date:
    """Return a date advanced by a number of calendar months."""
    if months < 0:
        raise ValidationError("Months to add cannot be negative.")

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
    remaining_amount: MoneyInput,
    monthly_contribution: MoneyInput,
) -> date | None:
    """Calculate the estimated completion date for a goal."""
    normalized_remaining = to_money(remaining_amount)
    normalized_contribution = to_money(monthly_contribution)

    if normalized_remaining < ZERO:
        raise ValidationError("Remaining goal amount cannot be negative.")

    if normalized_contribution < ZERO:
        raise ValidationError("Monthly contribution cannot be negative.")

    if normalized_remaining == ZERO:
        return as_of_date

    if normalized_contribution == ZERO:
        return None

    months_needed = math.ceil(normalized_remaining / normalized_contribution)

    return add_months(
        as_of_date,
        months_needed,
    )


def build_goal_projection(
    goal: Goal,
    *,
    target_date: date,
    planned_monthly_contribution: MoneyInput,
    as_of_date: date | None = None,
) -> GoalProjection:
    """Build a financial projection for one goal."""
    normalized_planned_contribution = to_money(planned_monthly_contribution)

    if normalized_planned_contribution < ZERO:
        raise ValidationError("Planned monthly contribution cannot be negative.")

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

    monthly_contribution_difference = subtract_money(
        normalized_planned_contribution,
        required_monthly_contribution,
    )

    projected_completion_date = calculate_projected_completion_date(
        as_of_date=effective_as_of_date,
        remaining_amount=remaining_amount,
        monthly_contribution=(normalized_planned_contribution),
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
        planned_monthly_contribution=(normalized_planned_contribution),
        monthly_contribution_difference=(monthly_contribution_difference),
        projected_completion_date=(projected_completion_date),
    )
