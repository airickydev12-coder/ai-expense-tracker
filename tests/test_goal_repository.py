from decimal import Decimal

import pytest

from src.financial.goals.models import Goal
from src.financial.goals.repository import (
    load_goals_from_file,
    save_goals_to_file,
)


def test_save_and_load_goals(db_path):
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
        db_path,
    )

    loaded_goals = load_goals_from_file(
        db_path,
    )

    assert loaded_goals == original_goals


def test_load_goals_returns_empty_list_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_goals.db"

    assert load_goals_from_file(db_path) == []


def test_save_goals_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "goals.db"

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
        load_goals_from_file(db_path)
