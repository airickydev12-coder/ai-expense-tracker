import json

import pytest

from src.financial.goals.models import Goal
from src.financial.goals.repository import (
    load_goals_from_file,
    save_goals_to_file,
)

from decimal import Decimal


def test_save_and_load_goals(tmp_path):
    file_path = tmp_path / "goals.json"

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
        file_path,
    )

    loaded_goals = load_goals_from_file(
        file_path,
    )

    assert loaded_goals == original_goals


def test_load_goals_returns_empty_list_when_file_missing(
    tmp_path,
):
    file_path = tmp_path / "missing_goals.json"

    assert load_goals_from_file(file_path) == []


def test_save_goals_creates_parent_directory(
    tmp_path,
):
    file_path = tmp_path / "nested" / "data" / "goals.json"

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
        file_path,
    )

    assert file_path.exists()


def test_load_goals_rejects_invalid_json(
    tmp_path,
):
    file_path = tmp_path / "goals.json"
    file_path.write_text(
        "not valid json",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="invalid JSON",
    ):
        load_goals_from_file(file_path)


def test_load_goals_rejects_non_list_json(
    tmp_path,
):
    file_path = tmp_path / "goals.json"
    file_path.write_text(
        json.dumps(
            {
                "id": 1,
                "name": "Emergency Fund",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="JSON list",
    ):
        load_goals_from_file(file_path)
