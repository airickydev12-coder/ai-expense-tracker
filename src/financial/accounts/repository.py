import json
from pathlib import Path

from src.core.config import DATA_DIR
from src.financial.accounts.models import Account


ACCOUNTS_FILE = DATA_DIR / "accounts.json"


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
        raise ValueError(
            f"Account data file contains invalid JSON: {file_path}"
        ) from error

    if not isinstance(raw_data, list):
        raise ValueError("Account data must be stored as a JSON list.")

    return [
        Account.from_dict(account_data)
        for account_data in raw_data
    ]


def save_accounts_to_file(
    accounts: list[Account],
    file_path: Path = ACCOUNTS_FILE,
) -> None:
    """Save accounts to a JSON file."""
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    account_data = [
        account.to_dict()
        for account in accounts
    ]

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            account_data,
            file,
            indent=4,
        )