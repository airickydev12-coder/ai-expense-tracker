import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError, ValidationError
from src.core.logging import get_logger
from src.financial.users.models import User

logger = get_logger(__name__)

_COLUMNS = "id, username, email, password_hash, is_active, created_at, updated_at"


def create_user(
    username: str,
    email: str,
    password_hash: str,
    db_path: Path = DB_PATH,
) -> User:
    """Insert a new user row, raising ValidationError on a duplicate username/email."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (username, email, password_hash, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
                """,
                (username, email, password_hash, now, now),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError as error:
        raise ValidationError(
            f"Username '{username}' or email '{email}' is already registered."
        ) from error
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to create user in {db_path}") from error

    logger.debug("Created user %d (%s) in %s", user_id, username, db_path)

    created_user = get_user_by_id(user_id, db_path) if user_id is not None else None
    if created_user is None:
        raise PersistenceError(f"Failed to reload newly created user in {db_path}")
    return created_user


def get_user_by_username(username: str, db_path: Path = DB_PATH) -> User | None:
    """Look up a user by username, returning None if not found."""
    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                f"SELECT {_COLUMNS} FROM users WHERE username = ?",
                (username,),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load user from {db_path}") from error

    return User.from_dict(dict(row)) if row is not None else None


def get_user_by_id(user_id: int, db_path: Path = DB_PATH) -> User | None:
    """Look up a user by id, returning None if not found."""
    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                f"SELECT {_COLUMNS} FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load user from {db_path}") from error

    return User.from_dict(dict(row)) if row is not None else None


def list_active_users(db_path: Path = DB_PATH) -> list[User]:
    """Return every active user, ordered by id.

    Used by the notification scheduler (src/api/main.py) to iterate every
    user's own check, since that job isn't tied to any one request.
    """
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                f"SELECT {_COLUMNS} FROM users WHERE is_active = 1 ORDER BY id"
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load users from {db_path}") from error

    return [User.from_dict(dict(row)) for row in rows]
