"""
One-time migration: assign every existing row in the user-owned tables to a
single "me" account, now that those tables have a nullable user_id column
(added in src/core/db.py's _ensure_user_id_columns).

Safe to re-run: only rows where user_id IS NULL are touched, and creating the
"me" user is a no-op if it already exists.

Run from the repo root as a module (so `src` resolves on sys.path):

    .venv/Scripts/python.exe -m scripts.backfill_user_id
"""

from __future__ import annotations

from src.core.config import DB_PATH
from src.core.db import _USER_OWNED_TABLES, get_connection, initialize_database
from src.core.exceptions import ValidationError
from src.financial.users import service as user_service
from src.financial.users.repository import get_user_by_username

ME_USERNAME = "me"
ME_EMAIL = "me@example.com"
ME_PASSWORD = "changeme-please-reset-1234"


def _ensure_me_user() -> int:
    """Return the id of the "me" account, creating it if it doesn't exist."""
    existing = get_user_by_username(ME_USERNAME)
    if existing is not None:
        return existing.id

    try:
        user = user_service.register_user(ME_USERNAME, ME_EMAIL, ME_PASSWORD)
    except ValidationError:
        # Another process created it between the check above and this call.
        existing = get_user_by_username(ME_USERNAME)
        assert existing is not None
        return existing.id

    print(
        f"Created '{ME_USERNAME}' account (id={user.id}) with a placeholder "
        f"password — reset it before relying on it for anything real."
    )
    return user.id


def backfill() -> None:
    """Assign every user-owned row with a NULL user_id to the "me" account."""
    initialize_database()
    me_id = _ensure_me_user()

    with get_connection(DB_PATH) as connection:
        for table in _USER_OWNED_TABLES:
            cursor = connection.execute(
                f"UPDATE {table} SET user_id = ? WHERE user_id IS NULL",
                (me_id,),
            )
            print(f"Backfilled {cursor.rowcount} row(s) in {table}")


if __name__ == "__main__":
    backfill()
