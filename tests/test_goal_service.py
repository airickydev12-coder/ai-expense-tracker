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


def setup_function():
    """Clear goal state before every test."""
    goals.clear()


def test_add_goal(tmp_path):
    file_path = tmp_path / "goals.json"

    goal = add_goal(
        name="Emergency Fund",
        target_amount=10000,
        current_amount=2500,
        file_path=file_path,
    )

    assert goal.id == 1
    assert goal.name == "Emergency Fund"
    assert goal.target_amount == 10000
    assert goal.current_amount == 2500
    assert file_path.exists()


def test_add_multiple_goals_assigns_unique_ids(
    tmp_path,
):
    file_path = tmp_path / "goals.json"

    first_goal = add_goal(
        name="Emergency Fund",
        target_amount=10000,
        file_path=file_path,
    )

    second_goal = add_goal(
        name="Vacation",
        target_amount=3000,
        file_path=file_path,
    )

    assert first_goal.id == 1
    assert second_goal.id == 2
    assert get_next_goal_id() == 3


def test_get_goals_returns_copy(
    tmp_path,
):
    file_path = tmp_path / "goals.json"

    add_goal(
        name="Emergency Fund",
        target_amount=10000,
        file_path=file_path,
    )

    returned_goals = get_goals()
    returned_goals.clear()

    assert len(goals) == 1


def test_get_goal_by_id(tmp_path):
    file_path = tmp_path / "goals.json"

    created_goal = add_goal(
        name="Emergency Fund",
        target_amount=10000,
        file_path=file_path,
    )

    assert get_goal_by_id(created_goal.id) == created_goal


def test_get_goal_by_id_returns_none():
    assert get_goal_by_id(999) is None


def test_update_goal(tmp_path):
    file_path = tmp_path / "goals.json"

    goal = add_goal(
        name="Emergency Fund",
        target_amount=10000,
        current_amount=2500,
        file_path=file_path,
    )

    updated_goal = update_goal(
        goal_id=goal.id,
        name="Primary Emergency Fund",
        target_amount=12000,
        file_path=file_path,
    )

    assert updated_goal is not None
    assert updated_goal.name == "Primary Emergency Fund"
    assert updated_goal.target_amount == 12000
    assert updated_goal.current_amount == 2500


def test_update_goal_preserves_unchanged_fields(
    tmp_path,
):
    file_path = tmp_path / "goals.json"

    goal = add_goal(
        name="Emergency Fund",
        target_amount=10000,
        current_amount=2500,
        file_path=file_path,
    )

    updated_goal = update_goal(
        goal_id=goal.id,
        current_amount=3000,
        file_path=file_path,
    )

    assert updated_goal is not None
    assert updated_goal.name == "Emergency Fund"
    assert updated_goal.target_amount == 10000
    assert updated_goal.current_amount == 3000


def test_update_goal_returns_none_when_missing(
    tmp_path,
):
    file_path = tmp_path / "goals.json"

    assert (
        update_goal(
            goal_id=999,
            name="Missing",
            file_path=file_path,
        )
        is None
    )


def test_contribute_to_goal(tmp_path):
    file_path = tmp_path / "goals.json"

    goal = add_goal(
        name="Emergency Fund",
        target_amount=10000,
        current_amount=2500,
        file_path=file_path,
    )

    updated_goal = contribute_to_goal(
        goal_id=goal.id,
        contribution=500,
        file_path=file_path,
    )

    assert updated_goal is not None
    assert updated_goal.current_amount == 3000


def test_contribution_does_not_exceed_target(
    tmp_path,
):
    file_path = tmp_path / "goals.json"

    goal = add_goal(
        name="Emergency Fund",
        target_amount=10000,
        current_amount=9500,
        file_path=file_path,
    )

    updated_goal = contribute_to_goal(
        goal_id=goal.id,
        contribution=1000,
        file_path=file_path,
    )

    assert updated_goal is not None
    assert updated_goal.current_amount == 10000


def test_negative_goal_contribution_raises_error(
    tmp_path,
):
    file_path = tmp_path / "goals.json"

    goal = add_goal(
        name="Emergency Fund",
        target_amount=10000,
        file_path=file_path,
    )

    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        contribute_to_goal(
            goal_id=goal.id,
            contribution=-100,
            file_path=file_path,
        )


def test_delete_goal(tmp_path):
    file_path = tmp_path / "goals.json"

    goal = add_goal(
        name="Emergency Fund",
        target_amount=10000,
        file_path=file_path,
    )

    deleted_goal = delete_goal(
        goal.id,
        file_path=file_path,
    )

    assert deleted_goal == goal
    assert get_goals() == []


def test_delete_goal_returns_none_when_missing(
    tmp_path,
):
    file_path = tmp_path / "goals.json"

    assert (
        delete_goal(
            999,
            file_path=file_path,
        )
        is None
    )


def test_load_goals_restores_saved_goals(
    tmp_path,
):
    file_path = tmp_path / "goals.json"

    add_goal(
        name="Emergency Fund",
        target_amount=10000,
        current_amount=2500,
        file_path=file_path,
    )

    goals.clear()

    load_goals(file_path)

    loaded_goals = get_goals()

    assert len(loaded_goals) == 1
    assert loaded_goals[0].name == "Emergency Fund"
    assert loaded_goals[0].current_amount == 2500