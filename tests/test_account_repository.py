from decimal import Decimal

import pytest

from src.financial.accounts.models import Account
from src.financial.accounts.repository import (
    load_accounts_from_file,
    save_accounts_to_file,
)


def test_save_and_load_accounts(db_path):
    original_accounts = [
        Account(
            id=1,
            name="Checking",
            account_type="Bank",
            balance=Decimal("1500"),
        ),
        Account(
            id=2,
            name="Savings",
            account_type="Bank",
            balance=Decimal("5000"),
        ),
    ]

    save_accounts_to_file(
        original_accounts,
        db_path,
    )

    loaded_accounts = load_accounts_from_file(
        db_path,
    )

    assert loaded_accounts == original_accounts


def test_load_accounts_returns_empty_list_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_accounts.db"

    loaded_accounts = load_accounts_from_file(
        db_path,
    )

    assert loaded_accounts == []


def test_save_accounts_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "accounts.db"

    accounts = [
        Account(
            id=1,
            name="Checking",
            account_type="Bank",
            balance=Decimal("1500"),
        )
    ]

    save_accounts_to_file(
        accounts,
        db_path,
    )

    assert db_path.exists()


def test_load_accounts_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "accounts.db"
    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load accounts",
    ):
        load_accounts_from_file(db_path)
