import pytest

from src.financial.goals.models import Goal


def test_goal_creation():
    goal = Goal(
        id=1,
        name="Emergency Fund",
        target_amount=10000,
        current_amount=2500,
    )

    assert goal.id == 1
    assert goal.name == "Emergency Fund"
    assert goal.target_amount == 10000
    assert goal.current_amount == 2500


def test_goal_invalid_id():
    with pytest.raises(ValueError):
        Goal(id=0, name="Emergency Fund", target_amount=10000, current_amount=2500)


def test_goal_empty_name():
    with pytest.raises(ValueError):
        Goal(id=1, name="", target_amount=10000, current_amount=2500)


def test_goal_invalid_target_amount():
    with pytest.raises(ValueError):
        Goal(id=1, name="Emergency Fund", target_amount=0, current_amount=2500)


def test_goal_negative_current_amount():
    with pytest.raises(ValueError):
        Goal(id=1, name="Emergency Fund", target_amount=10000, current_amount=-1)