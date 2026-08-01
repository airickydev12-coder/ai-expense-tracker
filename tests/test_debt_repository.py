from decimal import Decimal

import pytest

from src.financial.debt.models import Debt
from src.financial.debt.repository import (
    load_debts_from_file,
    save_debts_to_file,
)


def test_save_and_load_debts(db_path):
    original_debts = [
        Debt(
            id=1,
            name="Credit Card",
            balance=Decimal("2500.00"),
            interest_rate=24.99,
            minimum_payment=Decimal("75.00"),
        ),
        Debt(
            id=2,
            name="Car Loan",
            balance=Decimal("12000.00"),
            interest_rate=6.5,
            minimum_payment=Decimal("350.00"),
        ),
    ]

    save_debts_to_file(
        original_debts,
        db_path,
    )

    loaded_debts = load_debts_from_file(
        db_path,
    )

    assert loaded_debts == original_debts


def test_load_debts_returns_empty_list_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_debts.db"

    assert load_debts_from_file(db_path) == []


def test_save_debts_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "debts.db"

    debts = [
        Debt(
            id=1,
            name="Credit Card",
            balance=Decimal("2500.00"),
            interest_rate=24.99,
            minimum_payment=Decimal("75.00"),
        )
    ]

    save_debts_to_file(
        debts,
        db_path,
    )

    assert db_path.exists()


def test_load_debts_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "debts.db"
    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load debts",
    ):
        load_debts_from_file(db_path)
