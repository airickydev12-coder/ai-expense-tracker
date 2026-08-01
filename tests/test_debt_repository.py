import json
from decimal import Decimal

import pytest

from src.financial.debt.models import Debt
from src.financial.debt.repository import (
    load_debts_from_file,
    save_debts_to_file,
)


def test_save_and_load_debts(tmp_path):
    file_path = tmp_path / "debts.json"

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
        file_path,
    )

    loaded_debts = load_debts_from_file(
        file_path,
    )

    assert loaded_debts == original_debts


def test_load_debts_returns_empty_list_when_file_missing(
    tmp_path,
):
    file_path = tmp_path / "missing_debts.json"

    assert load_debts_from_file(file_path) == []


def test_save_debts_creates_parent_directory(
    tmp_path,
):
    file_path = tmp_path / "nested" / "data" / "debts.json"

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
        file_path,
    )

    assert file_path.exists()


def test_load_debts_rejects_invalid_json(
    tmp_path,
):
    file_path = tmp_path / "debts.json"
    file_path.write_text(
        "not valid json",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="invalid JSON",
    ):
        load_debts_from_file(file_path)


def test_load_debts_rejects_non_list_json(
    tmp_path,
):
    file_path = tmp_path / "debts.json"
    file_path.write_text(
        json.dumps(
            {
                "id": 1,
                "name": "Credit Card",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="JSON list",
    ):
        load_debts_from_file(file_path)
