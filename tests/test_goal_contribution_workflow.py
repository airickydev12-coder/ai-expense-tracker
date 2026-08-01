from decimal import Decimal

import pytest

from src.financial.goals.models import Goal
from src.financial.workflows.goal_contribution import apply_contribution_to_goal


def test_apply_contribution_to_goal():
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000"),
        current_amount=Decimal("2500"),
    )

    updated_goal = apply_contribution_to_goal(goal, Decimal("500"))

    assert updated_goal.current_amount == 3000


def test_goal_contribution_does_not_exceed_target():
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000"),
        current_amount=Decimal("9500"),
    )

    updated_goal = apply_contribution_to_goal(goal, Decimal("1000"))

    assert updated_goal.current_amount == 10000


def test_negative_goal_contribution():
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=Decimal("10000"),
        current_amount=Decimal("2500"),
    )

    with pytest.raises(ValueError):
        apply_contribution_to_goal(goal, Decimal("-100"))
