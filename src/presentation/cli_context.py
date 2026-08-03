"""
Resolves the single user the CLI presentation layer operates as.

The CLI (main.py) has no login flow — unlike the API, which is now
per-user (Stage B of the multi-user initiative), the CLI stays a
single-user tool that always operates as the "me" account created by
scripts/backfill_user_id.py.
"""

from src.core.exceptions import NotFoundError
from src.financial.users.repository import get_user_by_username

CLI_USERNAME = "me"

_cli_user_id: int | None = None


def get_cli_user_id() -> int:
    """Return the id of the "me" account the CLI always operates as."""
    global _cli_user_id

    if _cli_user_id is None:
        user = get_user_by_username(CLI_USERNAME)
        if user is None:
            raise NotFoundError(
                f"No '{CLI_USERNAME}' account exists yet — run "
                "`.venv/Scripts/python.exe -m scripts.backfill_user_id` first."
            )
        _cli_user_id = user.id

    return _cli_user_id
