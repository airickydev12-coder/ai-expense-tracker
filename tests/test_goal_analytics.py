from decimal import Decimal

from src.financial.goals.analytics import (
    get_goal_progress_percentage,
    get_remaining_goal_amount,
    get_total_goal_progress,
    get_total_goal_targets,
    is_goal_complete,
)
from src.financial.goals.models import Goal


def test_get_goal_progress_percentage():
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("2500.00"),
    )

    assert get_goal_progress_percentage(goal) == 25


def test_get_remaining_goal_amount():
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("2500.00"),
    )

    assert get_remaining_goal_amount(goal) == 7500


def test_is_goal_complete():
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("10000.00"),
    )

    assert is_goal_complete(goal) is True


def test_is_goal_not_complete():
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("2500.00"),
    )

    assert is_goal_complete(goal) is False


def test_get_total_goal_targets():
    goals = [
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("2500.00"),
        ),
        Goal(
            id=2,
            name="Vacation",
            target_amount=Decimal("3000.00"),
            current_amount=Decimal("500.00"),
        ),
    ]

    assert get_total_goal_targets(goals) == 13000


def test_get_total_goal_progress():
    goals = [
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("2500.00"),
        ),
        Goal(
            id=2,
            name="Vacation",
            target_amount=Decimal("3000.00"),
            current_amount=Decimal("500.00"),
        ),
    ]

    assert get_total_goal_progress(goals) == 3000
