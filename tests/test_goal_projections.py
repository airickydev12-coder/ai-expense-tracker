from datetime import date

import pytest

from src.financial.goals.models import Goal
from src.financial.goals.projections import (
    add_months,
    build_goal_projection,
    calculate_months_remaining,
    calculate_projected_completion_date,
    calculate_required_monthly_contribution,
)


def build_goal(
    *,
    current_amount: float = 4000,
) -> Goal:
    """Create a financial goal for projection tests."""
    return Goal(
        id=1,
        name="Emergency Fund",
        target_amount=10000,
        current_amount=current_amount,
    )


def test_calculate_months_remaining_same_day_next_year():
    result = calculate_months_remaining(
        date(2026, 7, 16),
        date(2027, 7, 16),
    )

    assert result == 12


def test_calculate_months_remaining_counts_partial_month():
    result = calculate_months_remaining(
        date(2026, 7, 16),
        date(2026, 8, 20),
    )

    assert result == 2


def test_calculate_months_remaining_same_month():
    result = calculate_months_remaining(
        date(2026, 7, 16),
        date(2026, 7, 31),
    )

    assert result == 1


def test_calculate_months_remaining_for_passed_date():
    result = calculate_months_remaining(
        date(2026, 7, 16),
        date(2026, 7, 1),
    )

    assert result == 0


def test_calculate_required_monthly_contribution():
    result = calculate_required_monthly_contribution(
        remaining_amount=6000,
        months_remaining=12,
    )

    assert result == 500


def test_required_contribution_for_completed_goal():
    result = calculate_required_monthly_contribution(
        remaining_amount=0,
        months_remaining=12,
    )

    assert result == 0


def test_required_contribution_when_deadline_passed():
    result = calculate_required_monthly_contribution(
        remaining_amount=6000,
        months_remaining=0,
    )

    assert result == 6000


def test_required_contribution_rejects_negative_amount():
    with pytest.raises(
        ValueError,
        match="Remaining",
    ):
        calculate_required_monthly_contribution(
            remaining_amount=-1,
            months_remaining=12,
        )


def test_add_months():
    result = add_months(
        date(2026, 7, 16),
        6,
    )

    assert result == date(
        2027,
        1,
        16,
    )


def test_add_months_adjusts_end_of_month():
    result = add_months(
        date(2026, 1, 31),
        1,
    )

    assert result == date(
        2026,
        2,
        28,
    )


def test_calculate_projected_completion_date():
    result = calculate_projected_completion_date(
        as_of_date=date(2026, 7, 16),
        remaining_amount=6000,
        monthly_contribution=600,
    )

    assert result == date(
        2027,
        5,
        16,
    )


def test_projected_completion_date_without_contribution():
    result = calculate_projected_completion_date(
        as_of_date=date(2026, 7, 16),
        remaining_amount=6000,
        monthly_contribution=0,
    )

    assert result is None


def test_completed_goal_projection_date_is_as_of_date():
    result = calculate_projected_completion_date(
        as_of_date=date(2026, 7, 16),
        remaining_amount=0,
        monthly_contribution=0,
    )

    assert result == date(
        2026,
        7,
        16,
    )


def test_build_goal_projection():
    projection = build_goal_projection(
        build_goal(),
        target_date=date(2027, 7, 16),
        planned_monthly_contribution=600,
        as_of_date=date(2026, 7, 16),
    )

    assert projection.goal_id == 1
    assert projection.remaining_amount == 6000
    assert projection.months_remaining == 12
    assert projection.required_monthly_contribution == 500
    assert projection.monthly_contribution_difference == 100
    assert projection.projected_completion_date == date(
        2027,
        5,
        16,
    )


def test_build_completed_goal_projection():
    projection = build_goal_projection(
        build_goal(
            current_amount=10000,
        ),
        target_date=date(2027, 7, 16),
        planned_monthly_contribution=0,
        as_of_date=date(2026, 7, 16),
    )

    assert projection.remaining_amount == 0
    assert projection.is_complete is True
    assert projection.projected_completion_date == date(
        2026,
        7,
        16,
    )


def test_build_goal_projection_rejects_negative_contribution():
    with pytest.raises(
        ValueError,
        match="Planned",
    ):
        build_goal_projection(
            build_goal(),
            target_date=date(2027, 7, 16),
            planned_monthly_contribution=-1,
            as_of_date=date(2026, 7, 16),
        )
