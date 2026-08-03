from decimal import Decimal
from pathlib import Path

from src.core.config import DB_PATH
from src.core.logging import get_logger
from src.financial.accounts.models import Account
from src.financial.accounts.repository import (
    load_accounts_from_file,
    save_accounts_to_file,
)

logger = get_logger(__name__)

accounts: dict[int, list[Account]] = {}


def _ensure_loaded(user_id: int, db_path: Path = DB_PATH) -> None:
    """Lazily load a user's accounts into the cache on first access."""
    if user_id not in accounts:
        accounts[user_id] = load_accounts_from_file(user_id, db_path)


def load_accounts(user_id: int, db_path: Path = DB_PATH) -> None:
    """Force-reload a user's accounts from the repository."""
    accounts[user_id] = load_accounts_from_file(user_id, db_path)


def save_accounts(user_id: int, db_path: Path = DB_PATH) -> None:
    """Save a user's accounts using the repository."""
    save_accounts_to_file(accounts[user_id], user_id, db_path)


def get_accounts(user_id: int, db_path: Path = DB_PATH) -> list[Account]:
    """Return a copy of all of this user's accounts."""
    _ensure_loaded(user_id, db_path)
    return accounts[user_id].copy()


def get_account_by_id(
    user_id: int,
    account_id: int,
    db_path: Path = DB_PATH,
) -> Account | None:
    """Return one of this user's accounts by its ID."""
    _ensure_loaded(user_id, db_path)

    for account in accounts[user_id]:
        if account.id == account_id:
            return account

    return None


def get_next_account_id(user_id: int) -> int:
    """Return the next available account ID for this user."""
    user_accounts = accounts.get(user_id, [])
    if not user_accounts:
        return 1

    return max(account.id for account in user_accounts) + 1


def add_account(
    user_id: int,
    name: str,
    account_type: str,
    balance: Decimal,
    db_path: Path = DB_PATH,
) -> Account:
    """Create and save a financial account for this user."""
    _ensure_loaded(user_id, db_path)

    account = Account(
        id=get_next_account_id(user_id),
        name=name,
        account_type=account_type,
        balance=balance,
    )

    accounts[user_id].append(account)
    save_accounts(user_id, db_path)

    logger.info(
        "Added account %d (%s) for user %d",
        account.id,
        account.name,
        user_id,
    )

    return account


def update_account(
    user_id: int,
    account_id: int,
    name: str | None = None,
    account_type: str | None = None,
    balance: Decimal | None = None,
    db_path: Path = DB_PATH,
) -> Account | None:
    """Update one of this user's existing accounts."""
    _ensure_loaded(user_id, db_path)

    account = get_account_by_id(user_id, account_id, db_path)

    if account is None:
        return None

    updated_name = name.strip() if name is not None else account.name

    updated_account_type = (
        account_type.strip() if account_type is not None else account.account_type
    )

    updated_balance = balance if balance is not None else account.balance

    updated_account = Account(
        id=account.id,
        name=updated_name,
        account_type=updated_account_type,
        balance=updated_balance,
    )

    account_index = accounts[user_id].index(account)
    accounts[user_id][account_index] = updated_account

    save_accounts(user_id, db_path)

    logger.info(
        "Updated account %d for user %d",
        account_id,
        user_id,
    )

    return updated_account


def delete_account(
    user_id: int,
    account_id: int,
    db_path: Path = DB_PATH,
) -> Account | None:
    """Delete one of this user's accounts by ID."""
    _ensure_loaded(user_id, db_path)

    for index, account in enumerate(accounts[user_id]):
        if account.id == account_id:
            deleted_account = accounts[user_id].pop(index)
            save_accounts(user_id, db_path)
            logger.info(
                "Deleted account %d for user %d",
                account_id,
                user_id,
            )
            return deleted_account

    return None
