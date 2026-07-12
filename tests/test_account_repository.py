import json

import pytest

from src.financial.accounts.models import Account
from src.financial.accounts.repository import (
    load_accounts_from_file,
    save_accounts_to_file,
)


def test_save_and_load_accounts(tmp_path):
    file_path = tmp_path / "accounts.json"

    original_accounts = [
        Account(
            id=1,
            name="Checking",
            account_type="Bank",
            balance=1500,
        ),
        Account(
            id=2,
            name="Savings",
            account_type="Bank",
            balance=5000,
        ),
    ]

    save_accounts_to_file(
        original_accounts,
        file_path,
    )

    loaded_accounts = load_accounts_from_file(
        file_path,
    )

    assert loaded_accounts == original_accounts


def test_load_accounts_returns_empty_list_when_file_missing(
    tmp_path,
):
    file_path = tmp_path / "missing_accounts.json"

    loaded_accounts = load_accounts_from_file(
        file_path,
    )

    assert loaded_accounts == []


def test_save_accounts_creates_parent_directory(
    tmp_path,
):
    file_path = (
        tmp_path
        / "nested"
        / "data"
        / "accounts.json"
    )

    accounts = [
        Account(
            id=1,
            name="Checking",
            account_type="Bank",
            balance=1500,
        )
    ]

    save_accounts_to_file(
        accounts,
        file_path,
    )

    assert file_path.exists()


def test_load_accounts_rejects_invalid_json(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"
    file_path.write_text(
        "not valid json",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="invalid JSON",
    ):
        load_accounts_from_file(file_path)


def test_load_accounts_rejects_non_list_json(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"
    file_path.write_text(
        json.dumps(
            {
                "id": 1,
                "name": "Checking",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="JSON list",
    ):
        load_accounts_from_file(file_path)