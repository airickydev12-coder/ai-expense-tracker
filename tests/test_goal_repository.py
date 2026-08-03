from decimal import Decimal

import pytest

from src.financial.goals.models import Goal
from src.financial.goals.repository import (
    load_goals_from_file,
    save_goals_to_file,
)
from src.financial.users.repository import create_user


def _create_user(db_path, username: str = "alice") -> int:
    user = create_user(username, f"{username}@example.com", "hashed-password", db_path)
    return user.id


def test_save_and_load_goals(db_path):
    user_id = _create_user(db_path)

    original_goals = [
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

    save_goals_to_file(
        original_goals,
        user_id,
        db_path,
    )

    loaded_goals = load_goals_from_file(
        user_id,
        db_path,
    )

    assert loaded_goals == original_goals


def test_load_goals_only_returns_matching_user(db_path):
    user_one_id = _create_user(db_path, "alice")
    user_two_id = _create_user(db_path, "bob")

    user_one_goals = [
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("2500.00"),
        ),
    ]
    user_two_goals = [
        Goal(
            id=1,
            name="Vacation",
            target_amount=Decimal("3000.00"),
            current_amount=Decimal("500.00"),
        ),
    ]

    save_goals_to_file(user_one_goals, user_one_id, db_path)
    save_goals_to_file(user_two_goals, user_two_id, db_path)

    assert load_goals_from_file(user_one_id, db_path) == user_one_goals
    assert load_goals_from_file(user_two_id, db_path) == user_two_goals


def test_load_goals_returns_empty_list_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_goals.db"

    assert load_goals_from_file(1, db_path) == []


def test_save_goals_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "goals.db"
    user_id = _create_user(db_path)

    goals = [
        Goal(
            id=1,
            name="Emergency Fund",
            target_amount=Decimal("10000.00"),
            current_amount=Decimal("2500.00"),
        )
    ]

    save_goals_to_file(
        goals,
        user_id,
        db_path,
    )

    assert db_path.exists()


def test_load_goals_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "goals.db"
    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load goals",
    ):
        load_goals_from_file(1, db_path)
