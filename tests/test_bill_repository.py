import json
from decimal import Decimal

import pytest

from src.financial.bills.models import Bill
from src.financial.bills.repository import (
    load_bills_from_file,
    save_bills_to_file,
)


def test_save_and_load_bills(tmp_path):
    file_path = tmp_path / "bills.json"

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
        file_path,
    )

    loaded_bills = load_bills_from_file(
        file_path,
    )

    assert loaded_bills == original_bills


def test_load_bills_returns_empty_list_when_file_missing(
    tmp_path,
):
    file_path = tmp_path / "missing_bills.json"

    assert load_bills_from_file(file_path) == []


def test_save_bills_creates_parent_directory(
    tmp_path,
):
    file_path = tmp_path / "nested" / "data" / "bills.json"

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
        file_path,
    )

    assert file_path.exists()


def test_load_bills_rejects_invalid_json(
    tmp_path,
):
    file_path = tmp_path / "bills.json"
    file_path.write_text(
        "not valid json",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="invalid JSON",
    ):
        load_bills_from_file(file_path)


def test_load_bills_rejects_non_list_json(
    tmp_path,
):
    file_path = tmp_path / "bills.json"
    file_path.write_text(
        json.dumps(
            {
                "id": 1,
                "name": "Electric",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="JSON list",
    ):
        load_bills_from_file(file_path)
