from decimal import Decimal

from src.financial.accounts.models import Account
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
from src.financial.users.repository import create_user

USER_ID = 1


def setup_function():
    """Clear account state before every test."""
    accounts.clear()


def _create_user(file_path) -> None:
    """Insert a throwaway user row so accounts' FK constraint is satisfied."""
    create_user("alice", "alice@example.com", "hash", file_path)


def test_add_account(tmp_path):
    file_path = tmp_path / "accounts.json"
    _create_user(file_path)

    account = add_account(
        user_id=USER_ID,
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        db_path=file_path,
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
    _create_user(file_path)

    first_account = add_account(
        user_id=USER_ID,
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        db_path=file_path,
    )

    second_account = add_account(
        user_id=USER_ID,
        name="Savings",
        account_type="Bank",
        balance=Decimal("5000"),
        db_path=file_path,
    )

    assert first_account.id == 1
    assert second_account.id == 2
    assert get_next_account_id(USER_ID) == 3


def test_get_accounts_returns_copy(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"
    _create_user(file_path)

    add_account(
        user_id=USER_ID,
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        db_path=file_path,
    )

    returned_accounts = get_accounts(USER_ID, db_path=file_path)
    returned_accounts.clear()

    assert len(accounts[USER_ID]) == 1


def test_get_account_by_id(tmp_path):
    file_path = tmp_path / "accounts.json"
    _create_user(file_path)

    created_account = add_account(
        user_id=USER_ID,
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        db_path=file_path,
    )

    found_account = get_account_by_id(USER_ID, created_account.id, db_path=file_path)

    assert found_account == created_account


def test_get_account_by_id_returns_none(tmp_path):
    file_path = tmp_path / "accounts.json"
    _create_user(file_path)

    assert get_account_by_id(USER_ID, 999, db_path=file_path) is None


def test_update_account(tmp_path):
    file_path = tmp_path / "accounts.json"
    _create_user(file_path)

    account = add_account(
        user_id=USER_ID,
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        db_path=file_path,
    )

    updated_account = update_account(
        user_id=USER_ID,
        account_id=account.id,
        name="Primary Checking",
        balance=Decimal("2000"),
        db_path=file_path,
    )

    assert updated_account is not None
    assert updated_account.name == "Primary Checking"
    assert updated_account.account_type == "Bank"
    assert updated_account.balance == Decimal("2000")


def test_update_account_preserves_unchanged_fields(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"
    _create_user(file_path)

    account = add_account(
        user_id=USER_ID,
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        db_path=file_path,
    )

    updated_account = update_account(
        user_id=USER_ID,
        account_id=account.id,
        balance=Decimal("1800"),
        db_path=file_path,
    )

    assert updated_account is not None
    assert updated_account.name == "Checking"
    assert updated_account.account_type == "Bank"
    assert updated_account.balance == 1800


def test_update_account_returns_none_when_missing(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"
    _create_user(file_path)

    result = update_account(
        user_id=USER_ID,
        account_id=999,
        name="Missing",
        db_path=file_path,
    )

    assert result is None


def test_delete_account(tmp_path):
    file_path = tmp_path / "accounts.json"
    _create_user(file_path)

    account = add_account(
        user_id=USER_ID,
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        db_path=file_path,
    )

    deleted_account = delete_account(
        USER_ID,
        account.id,
        db_path=file_path,
    )

    assert deleted_account == account
    assert get_accounts(USER_ID, db_path=file_path) == []


def test_delete_account_returns_none_when_missing(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"
    _create_user(file_path)

    result = delete_account(
        USER_ID,
        999,
        db_path=file_path,
    )

    assert result is None


def test_load_accounts_restores_saved_accounts(
    tmp_path,
):
    file_path = tmp_path / "accounts.json"
    _create_user(file_path)

    add_account(
        user_id=USER_ID,
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
        db_path=file_path,
    )

    # Mutate the in-memory cache directly without persisting, to prove
    # load_accounts() force-reloads from disk rather than trusting the cache.
    accounts[USER_ID].append(
        Account(id=999, name="Ghost", account_type="Bank", balance=Decimal("0"))
    )
    assert len(accounts[USER_ID]) == 2

    load_accounts(USER_ID, file_path)

    loaded_accounts = get_accounts(USER_ID, db_path=file_path)

    assert len(loaded_accounts) == 1
    assert loaded_accounts[0].name == "Checking"
    assert loaded_accounts[0].balance == Decimal("1500")
