from src.financial.accounts.service import (
    accounts,
    add_account,
    delete_account,
    get_account_by_id,
    get_accounts,
    get_next_account_id,
    load_accounts,
    update_account,
)
from decimal import Decimal


def setup_function():
    """Clear account state before every test."""
    accounts.clear()


def test_add_account(tmp_path):
    file_path = tmp_path / "accounts.json"

    account = add_account(
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        file_path=file_path,
    )

    assert account.id == 1
    assert account.name == "Checking"
    assert account.account_type == "Bank"
    assert account.balance == 1500
    assert file_path.exists()


def test_add_multiple_accounts_assigns_unique_ids(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"

    first_account = add_account(
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        file_path=file_path,
    )

    second_account = add_account(
        name="Savings",
        account_type="Bank",
        balance=Decimal("5000"),
        file_path=file_path,
    )

    assert first_account.id == 1
    assert second_account.id == 2
    assert get_next_account_id() == 3


def test_get_accounts_returns_copy(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"

    add_account(
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        file_path=file_path,
    )

    returned_accounts = get_accounts()
    returned_accounts.clear()

    assert len(accounts) == 1


def test_get_account_by_id(tmp_path):
    file_path = tmp_path / "accounts.json"

    created_account = add_account(
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        file_path=file_path,
    )

    found_account = get_account_by_id(created_account.id)

    assert found_account == created_account


def test_get_account_by_id_returns_none():
    assert get_account_by_id(999) is None


def test_update_account(tmp_path):
    file_path = tmp_path / "accounts.json"

    account = add_account(
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        file_path=file_path,
    )

    updated_account = update_account(
        account_id=account.id,
        name="Primary Checking",
        balance=Decimal("2000"),
        file_path=file_path,
    )

    assert updated_account is not None
    assert updated_account.name == "Primary Checking"
    assert updated_account.account_type == "Bank"
    assert updated_account.balance == Decimal("2000")


def test_update_account_preserves_unchanged_fields(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"

    account = add_account(
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        file_path=file_path,
    )

    updated_account = update_account(
        account_id=account.id,
        balance=Decimal("1800"),
        file_path=file_path,
    )

    assert updated_account is not None
    assert updated_account.name == "Checking"
    assert updated_account.account_type == "Bank"
    assert updated_account.balance == 1800


def test_update_account_returns_none_when_missing(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"

    result = update_account(
        account_id=999,
        name="Missing",
        file_path=file_path,
    )

    assert result is None


def test_delete_account(tmp_path):
    file_path = tmp_path / "accounts.json"

    account = add_account(
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        file_path=file_path,
    )

    deleted_account = delete_account(
        account.id,
        file_path=file_path,
    )

    assert deleted_account == account
    assert get_accounts() == []


def test_delete_account_returns_none_when_missing(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"

    result = delete_account(
        999,
        file_path=file_path,
    )

    assert result is None


def test_load_accounts_restores_saved_accounts(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"

    add_account(
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        file_path=file_path,
    )

    accounts.clear()

    assert get_accounts() == []

    load_accounts(file_path)

    loaded_accounts = get_accounts()

    assert len(loaded_accounts) == 1
    assert loaded_accounts[0].name == "Checking"
    assert loaded_accounts[0].balance == Decimal("1500")
