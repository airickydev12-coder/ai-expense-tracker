from decimal import Decimal

import pytest

from src.financial.budgets.models import Budget
from src.financial.budgets.repository import (
    load_budgets_from_file,
    save_budgets_to_file,
)
from src.financial.shared.categories import ExpenseCategory


def test_save_and_load_budgets(db_path):
    original_budgets = [
        Budget(
            category=ExpenseCategory.FOOD,
            limit=Decimal("400.00"),
        ),
        Budget(
            category=ExpenseCategory.TRANSPORTATION,
            limit=Decimal("150.00"),
        ),
    ]

    save_budgets_to_file(
        original_budgets,
        db_path,
    )

    loaded_budgets = load_budgets_from_file(
        db_path,
    )

    assert loaded_budgets == original_budgets


def test_load_budgets_returns_empty_list_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_budgets.db"

    assert load_budgets_from_file(db_path) == []


def test_save_budgets_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "budgets.db"

    budgets = [
        Budget(
            category=ExpenseCategory.FOOD,
            limit=Decimal("400.00"),
        )
    ]

    save_budgets_to_file(
        budgets,
        db_path,
    )

    assert db_path.exists()


def test_load_budgets_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "budgets.db"
    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load budgets",
    ):
        load_budgets_from_file(db_path)
