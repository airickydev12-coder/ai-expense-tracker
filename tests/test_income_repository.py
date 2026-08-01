from decimal import Decimal

import pytest

from src.financial.income.models import Income
from src.financial.income.repository import (
    load_income_from_file,
    save_income_to_file,
)


def test_save_and_load_income(db_path):
    original_income = [
        Income(
            id=1,
            source="Salary",
            amount=Decimal("3000.00"),
        ),
        Income(
            id=2,
            source="Freelance",
            amount=Decimal("500.00"),
        ),
    ]

    save_income_to_file(
        original_income,
        db_path,
    )

    loaded_income = load_income_from_file(
        db_path,
    )

    assert loaded_income == original_income


def test_load_income_returns_empty_list_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_income.db"

    assert load_income_from_file(db_path) == []


def test_save_income_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "income.db"

    income_entries = [
        Income(
            id=1,
            source="Salary",
            amount=Decimal("3000.00"),
        )
    ]

    save_income_to_file(
        income_entries,
        db_path,
    )

    assert db_path.exists()


def test_load_income_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "income.db"
    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load income",
    ):
        load_income_from_file(db_path)
