import json
from pathlib import Path

from src.core.config import ACCOUNTS_FILE
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.accounts.models import Account

logger = get_logger(__name__)


def load_accounts_from_file(
    file_path: Path = ACCOUNTS_FILE,
) -> list[Account]:
    """Load accounts from a JSON file."""
    if not file_path.exists():
        return []

    try:
        with file_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError as error:
        logger.error(
            "Failed to parse accounts file %s: %s",
            file_path,
            error,
        )
        raise PersistenceError(
            f"Account data file contains invalid JSON: {file_path}"
        ) from error

    if not isinstance(raw_data, list):
        raise PersistenceError("Account data must be stored as a JSON list.")

    accounts = [Account.from_dict(account_data) for account_data in raw_data]

    logger.debug(
        "Loaded %d account(s) from %s",
        len(accounts),
        file_path,
    )

    return accounts


def save_accounts_to_file(
    accounts: list[Account],
    file_path: Path = ACCOUNTS_FILE,
) -> None:
    """Save accounts to a JSON file."""
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    account_data = [account.to_dict() for account in accounts]

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            account_data,
            file,
            indent=4,
        )

    logger.debug(
        "Saved %d account(s) to %s",
        len(accounts),
        file_path,
    )
