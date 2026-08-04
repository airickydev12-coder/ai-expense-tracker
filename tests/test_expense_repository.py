from decimal import Decimal

import pytest

from src.financial.expenses.models import Expense
from src.financial.expenses.repository import (
    load_expenses_from_file,
    save_expenses_to_file,
)
from src.financial.shared.categories import ExpenseCategory


def test_save_and_load_expenses(db_path):
    original_expenses = [
        Expense(
            id=1,
            name="Coffee",
            category=ExpenseCategory.FOOD,
            amount=Decimal("5.25"),
        ),
        Expense(
            id=2,
            name="Gas",
            category=ExpenseCategory.TRANSPORTATION,
            amount=Decimal("40.00"),
        ),
    ]

    save_expenses_to_file(
        original_expenses,
        1,
        db_path,
    )

    loaded_expenses = load_expenses_from_file(
        1,
        db_path,
    )

    assert loaded_expenses == original_expenses


def test_load_expenses_returns_empty_list_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_expenses.db"

    assert load_expenses_from_file(1, db_path) == []


def test_save_expenses_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "expenses.db"

    expenses = [
        Expense(
            id=1,
            name="Coffee",
            category=ExpenseCategory.FOOD,
            amount=Decimal("5.25"),
        )
    ]

    save_expenses_to_file(
        expenses,
        1,
        db_path,
    )

    assert db_path.exists()


def test_load_expenses_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "expenses.db"
    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load expenses",
    ):
        load_expenses_from_file(1, db_path)
