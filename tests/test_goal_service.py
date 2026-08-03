from decimal import Decimal

import pytest

from src.financial.goals.service import (
    add_goal,
    contribute_to_goal,
    delete_goal,
    get_goal_by_id,
    get_goals,
    get_next_goal_id,
    goals,
    load_goals,
    update_goal,
)
from src.financial.users.repository import create_user


def setup_function():
    """Clear goal state before every test."""
    goals.clear()


def _create_user(file_path, username: str = "alice") -> int:
    user = create_user(username, f"{username}@example.com", "hashed-password", file_path)
    return user.id


def test_add_goal(tmp_path):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    goal = add_goal(
        user_id=user_id,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("2500.00"),
        file_path=file_path,
    )

    assert goal.id == 1
    assert goal.name == "Emergency Fund"
    assert goal.target_amount == Decimal("10000.00")
    assert goal.current_amount == Decimal("2500.00")
    assert file_path.exists()


def test_add_multiple_goals_assigns_unique_ids(
    tmp_path,
):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    first_goal = add_goal(
        user_id=user_id,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        file_path=file_path,
    )

    second_goal = add_goal(
        user_id=user_id,
        name="Vacation",
        target_amount=Decimal("3000.00"),
        file_path=file_path,
    )

    assert first_goal.id == 1
    assert second_goal.id == 2
    assert get_next_goal_id(user_id) == 3


def test_add_goal_scopes_ids_per_user(
    tmp_path,
):
    file_path = tmp_path / "goals.db"
    user_one_id = _create_user(file_path, "alice")
    user_two_id = _create_user(file_path, "bob")

    user_one_goal = add_goal(
        user_id=user_one_id,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        file_path=file_path,
    )

    user_two_goal = add_goal(
        user_id=user_two_id,
        name="Vacation",
        target_amount=Decimal("3000.00"),
        file_path=file_path,
    )

    assert user_one_goal.id == 1
    assert user_two_goal.id == 1
    assert get_goals(user_one_id) == [user_one_goal]
    assert get_goals(user_two_id) == [user_two_goal]


def test_get_goals_returns_copy(
    tmp_path,
):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    add_goal(
        user_id=user_id,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        file_path=file_path,
    )

    returned_goals = get_goals(user_id)
    returned_goals.clear()

    assert len(goals[user_id]) == 1


def test_get_goal_by_id(tmp_path):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    created_goal = add_goal(
        user_id=user_id,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        file_path=file_path,
    )

    assert get_goal_by_id(user_id, created_goal.id) == created_goal


def test_get_goal_by_id_returns_none(tmp_path):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    assert get_goal_by_id(user_id, 999, file_path) is None


def test_update_goal(tmp_path):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    goal = add_goal(
        user_id=user_id,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("2500.00"),
        file_path=file_path,
    )

    updated_goal = update_goal(
        user_id=user_id,
        goal_id=goal.id,
        name="Primary Emergency Fund",
        target_amount=Decimal("12000.00"),
        file_path=file_path,
    )

    assert updated_goal is not None
    assert updated_goal.name == "Primary Emergency Fund"
    assert updated_goal.target_amount == Decimal("12000.00")
    assert updated_goal.current_amount == Decimal("2500.00")


def test_update_goal_preserves_unchanged_fields(
    tmp_path,
):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    goal = add_goal(
        user_id=user_id,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("2500.00"),
        file_path=file_path,
    )

    updated_goal = update_goal(
        user_id=user_id,
        goal_id=goal.id,
        current_amount=Decimal("3000.00"),
        file_path=file_path,
    )

    assert updated_goal is not None
    assert updated_goal.name == "Emergency Fund"
    assert updated_goal.target_amount == Decimal("10000.00")
    assert updated_goal.current_amount == Decimal("3000.00")


def test_update_goal_returns_none_when_missing(
    tmp_path,
):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    assert (
        update_goal(
            user_id=user_id,
            goal_id=999,
            name="Missing",
            file_path=file_path,
        )
        is None
    )


def test_contribute_to_goal(tmp_path):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    goal = add_goal(
        user_id=user_id,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("2500.00"),
        file_path=file_path,
    )

    updated_goal = contribute_to_goal(
        user_id=user_id,
        goal_id=goal.id,
        contribution=5000,
        file_path=file_path,
    )

    assert updated_goal is not None
    assert updated_goal.current_amount == Decimal("7500.00")


def test_contribution_does_not_exceed_target(
    tmp_path,
):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    goal = add_goal(
        user_id=user_id,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("9500.00"),
        file_path=file_path,
    )

    updated_goal = contribute_to_goal(
        user_id=user_id,
        goal_id=goal.id,
        contribution=1000,
        file_path=file_path,
    )

    assert updated_goal is not None
    assert updated_goal.current_amount == Decimal("10000.00")


def test_negative_goal_contribution_raises_error(
    tmp_path,
):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    goal = add_goal(
        user_id=user_id,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        file_path=file_path,
    )

    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        contribute_to_goal(
            user_id=user_id,
            goal_id=goal.id,
            contribution=-100,
            file_path=file_path,
        )


def test_delete_goal(tmp_path):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    goal = add_goal(
        user_id=user_id,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        file_path=file_path,
    )

    deleted_goal = delete_goal(
        user_id,
        goal.id,
        file_path=file_path,
    )

    assert deleted_goal == goal
    assert get_goals(user_id) == []


def test_delete_goal_returns_none_when_missing(
    tmp_path,
):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    assert (
        delete_goal(
            user_id,
            999,
            file_path=file_path,
        )
        is None
    )


def test_load_goals_restores_saved_goals(
    tmp_path,
):
    file_path = tmp_path / "goals.db"
    user_id = _create_user(file_path)

    add_goal(
        user_id=user_id,
        name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("2500.00"),
        file_path=file_path,
    )

    goals.clear()

    load_goals(user_id, file_path)

    loaded_goals = get_goals(user_id)

    assert len(loaded_goals) == 1
    assert loaded_goals[0].name == "Emergency Fund"
    assert loaded_goals[0].current_amount == Decimal("2500.00")
