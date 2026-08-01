from decimal import Decimal

import pytest

from src.financial.bills.models import Bill
from src.financial.bills.repository import (
    load_bills_from_file,
    save_bills_to_file,
)


def test_save_and_load_bills(db_path):
    original_bills = [
        Bill(
            id=1,
            name="Electric",
            amount=Decimal("125.00"),
            due_day=15,
            is_paid=False,
        ),
        Bill(
            id=2,
            name="Internet",
            amount=Decimal("80.00"),
            due_day=20,
            is_paid=True,
        ),
    ]

    save_bills_to_file(
        original_bills,
        db_path,
    )

    loaded_bills = load_bills_from_file(
        db_path,
    )

    assert loaded_bills == original_bills


def test_load_bills_returns_empty_list_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_bills.db"

    assert load_bills_from_file(db_path) == []


def test_save_bills_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "bills.db"

    bills = [
        Bill(
            id=1,
            name="Electric",
            amount=Decimal("125.00"),
            due_day=15,
            is_paid=False,
        )
    ]

    save_bills_to_file(
        bills,
        db_path,
    )

    assert db_path.exists()


def test_load_bills_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "bills.db"
    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load bills",
    ):
        load_bills_from_file(db_path)
