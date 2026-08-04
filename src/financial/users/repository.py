import sqlite3
from datetime import datetime, timedelta, timezone
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


def update_user(
    user_id: int,
    *,
    username: str | None = None,
    email: str | None = None,
    db_path: Path = DB_PATH,
) -> User:
    """Update a user's username and/or email, raising ValidationError on a conflict."""
    now = datetime.now(timezone.utc).isoformat()

    fields: list[str] = []
    values: list[str] = []

    if username is not None:
        fields.append("username = ?")
        values.append(username)

    if email is not None:
        fields.append("email = ?")
        values.append(email)

    fields.append("updated_at = ?")
    values.append(now)
    values.append(str(user_id))

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                f"UPDATE users SET {', '.join(fields)} WHERE id = ?",
                values,
            )
    except sqlite3.IntegrityError as error:
        raise ValidationError(
            f"Username '{username}' or email '{email}' is already registered."
        ) from error
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to update user {user_id} in {db_path}") from error

    logger.debug("Updated user %d in %s", user_id, db_path)

    updated_user = get_user_by_id(user_id, db_path)
    if updated_user is None:
        raise PersistenceError(f"Failed to reload updated user {user_id} in {db_path}")
    return updated_user


def update_password_hash(user_id: int, password_hash: str, db_path: Path = DB_PATH) -> None:
    """Overwrite a user's stored password hash."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                (password_hash, now, user_id),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to update password for user {user_id} in {db_path}") from error

    logger.debug("Updated password hash for user %d in %s", user_id, db_path)


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


def get_user_by_email(email: str, db_path: Path = DB_PATH) -> User | None:
    """Look up a user by email, returning None if not found."""
    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                f"SELECT {_COLUMNS} FROM users WHERE email = ?",
                (email,),
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


def record_login_attempt(username: str, succeeded: bool, db_path: Path = DB_PATH) -> None:
    """Record one login attempt (success or failure) for a username."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "INSERT INTO login_attempts (username, attempted_at, succeeded) VALUES (?, ?, ?)",
                (username, now, int(succeeded)),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to record login attempt in {db_path}") from error


def count_recent_failed_attempts(
    username: str, window_minutes: int, db_path: Path = DB_PATH
) -> int:
    """Count a username's failed login attempts within the trailing window."""
    since = (datetime.now(timezone.utc) - timedelta(minutes=window_minutes)).isoformat()

    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count FROM login_attempts
                WHERE username = ? AND succeeded = 0 AND attempted_at > ?
                """,
                (username, since),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to count login attempts in {db_path}") from error

    return int(row["count"])


def record_password_reset_request(email: str, db_path: Path = DB_PATH) -> None:
    """Record one password reset request for an email address."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "INSERT INTO password_reset_requests (email, requested_at) VALUES (?, ?)",
                (email, now),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to record password reset request in {db_path}") from error


def count_recent_password_reset_requests(
    email: str, window_minutes: int, db_path: Path = DB_PATH
) -> int:
    """Count an email's password reset requests within the trailing window."""
    since = (datetime.now(timezone.utc) - timedelta(minutes=window_minutes)).isoformat()

    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count FROM password_reset_requests
                WHERE email = ? AND requested_at > ?
                """,
                (email, since),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to count password reset requests in {db_path}") from error

    return int(row["count"])


def create_password_reset_token(
    user_id: int, token_hash: str, expires_at: str, db_path: Path = DB_PATH
) -> None:
    """Insert a new password reset token row for a user."""
    try:
        with get_connection(db_path) as connection:
            connection.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token_hash, expires_at, used_at)
                VALUES (?, ?, ?, NULL)
                """,
                (user_id, token_hash, expires_at),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to create password reset token in {db_path}") from error


def get_password_reset_token(token_hash: str, db_path: Path = DB_PATH) -> dict | None:
    """Look up an unexpired, unused password reset token by its hash.

    Returns a plain dict (id, user_id, expires_at) rather than a domain model,
    since this row has no dataclass of its own -- it's purely a lookup table.
    """
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                """
                SELECT id, user_id, expires_at FROM password_reset_tokens
                WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?
                """,
                (token_hash, now),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load password reset token from {db_path}") from error

    return dict(row) if row is not None else None


def mark_password_reset_token_used(token_id: int, db_path: Path = DB_PATH) -> None:
    """Mark a password reset token as used, so it can't be redeemed again."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "UPDATE password_reset_tokens SET used_at = ? WHERE id = ?",
                (now, token_id),
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to mark password reset token {token_id} used in {db_path}"
        ) from error


def create_refresh_token(
    user_id: int, token_hash: str, issued_at: str, expires_at: str, db_path: Path = DB_PATH
) -> None:
    """Insert a new refresh token row for a user."""
    try:
        with get_connection(db_path) as connection:
            connection.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, issued_at, expires_at, revoked_at)
                VALUES (?, ?, ?, ?, NULL)
                """,
                (user_id, token_hash, issued_at, expires_at),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to create refresh token in {db_path}") from error


def get_refresh_token(token_hash: str, db_path: Path = DB_PATH) -> dict | None:
    """Look up an unrevoked, unexpired refresh token by its hash.

    Returns a plain dict (id, user_id) rather than a domain model, since
    this row has no dataclass of its own -- it's purely a lookup table.
    """
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                """
                SELECT id, user_id FROM refresh_tokens
                WHERE token_hash = ? AND revoked_at IS NULL AND expires_at > ?
                """,
                (token_hash, now),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load refresh token from {db_path}") from error

    return dict(row) if row is not None else None


def revoke_refresh_token(token_hash: str, db_path: Path = DB_PATH) -> None:
    """Revoke a refresh token by its hash, so it can no longer be used or rotated."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "UPDATE refresh_tokens SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
                (now, token_hash),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to revoke refresh token in {db_path}") from error


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
