from decimal import Decimal
from pathlib import Path

from src.core.logging import get_logger
from src.financial.accounts.models import Account
from src.financial.accounts.repository import (
    ACCOUNTS_FILE,
    load_accounts_from_file,
    save_accounts_to_file,
)

logger = get_logger(__name__)

accounts: list[Account] = []


def load_accounts(
    file_path: Path = ACCOUNTS_FILE,
) -> None:
    """Load accounts into application memory."""
    accounts.clear()
    accounts.extend(load_accounts_from_file(file_path))


def save_accounts(
    file_path: Path = ACCOUNTS_FILE,
) -> None:
    """Save all accounts from application memory."""
    save_accounts_to_file(
        accounts,
        file_path,
    )


def get_accounts() -> list[Account]:
    """Return a copy of all accounts."""
    return accounts.copy()


def get_account_by_id(
    account_id: int,
) -> Account | None:
    """Return an account by ID."""
    for account in accounts:
        if account.id == account_id:
            return account

    return None


def get_next_account_id() -> int:
    """Return the next available account ID."""
    if not accounts:
        return 1

    return max(account.id for account in accounts) + 1


def add_account(
    name: str,
    account_type: str,
    balance: Decimal,
    file_path: Path = ACCOUNTS_FILE,
) -> Account:
    """Create and save a financial account."""
    account = Account(
        id=get_next_account_id(),
        name=name,
        account_type=account_type,
        balance=balance,
    )

    accounts.append(account)
    save_accounts(file_path)

    logger.info(
        "Added account %d (%s)",
        account.id,
        account.name,
    )

    return account


def update_account(
    account_id: int,
    name: str | None = None,
    account_type: str | None = None,
    balance: Decimal | None = None,
    file_path: Path = ACCOUNTS_FILE,
) -> Account | None:
    """Update an existing account."""
    account = get_account_by_id(account_id)

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

    account_index = accounts.index(account)
    accounts[account_index] = updated_account

    save_accounts(file_path)

    logger.info(
        "Updated account %d",
        account_id,
    )

    return updated_account


def delete_account(
    account_id: int,
    file_path: Path = ACCOUNTS_FILE,
) -> Account | None:
    """Delete an account by ID."""
    for index, account in enumerate(accounts):
        if account.id == account_id:
            deleted_account = accounts.pop(index)
            save_accounts(file_path)
            logger.info(
                "Deleted account %d",
                account_id,
            )
            return deleted_account

    return None
