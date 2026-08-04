import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError, ValidationError
from src.core.logging import get_logger
from src.financial.users.models import User
from src.financial.users.role import PlatformRole

logger = get_logger(__name__)

_COLUMNS = (
    "id, username, email, password_hash, is_active, role, created_at, updated_at, "
    "email_verified_at"
)


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


def update_user_role(user_id: int, role: PlatformRole, db_path: Path = DB_PATH) -> User:
    """Overwrite a user's platform role.

    Deliberately separate from update_user() -- role assignment is a
    privileged admin action, not a self-service profile edit, and shouldn't
    share a code path (or authorization assumptions) with one.
    """
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "UPDATE users SET role = ?, updated_at = ? WHERE id = ?",
                (role.value, now, user_id),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to update role for user {user_id} in {db_path}") from error

    logger.debug("Updated role for user %d to %s in %s", user_id, role.value, db_path)

    updated_user = get_user_by_id(user_id, db_path)
    if updated_user is None:
        raise PersistenceError(f"Failed to reload updated user {user_id} in {db_path}")
    return updated_user


def update_user_active_status(user_id: int, is_active: bool, db_path: Path = DB_PATH) -> User:
    """Overwrite a user's is_active flag.

    Deliberately separate from update_user(), mirroring update_user_role()
    above -- activation/deactivation is a privileged admin action, not a
    self-service profile edit, and shouldn't share a code path (or
    authorization assumptions) with one.
    """
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "UPDATE users SET is_active = ?, updated_at = ? WHERE id = ?",
                (int(is_active), now, user_id),
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to update active status for user {user_id} in {db_path}"
        ) from error

    logger.debug("Updated active status for user %d to %s in %s", user_id, is_active, db_path)

    updated_user = get_user_by_id(user_id, db_path)
    if updated_user is None:
        raise PersistenceError(f"Failed to reload updated user {user_id} in {db_path}")
    return updated_user


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


def create_email_verification_token(
    user_id: int, token_hash: str, expires_at: str, db_path: Path = DB_PATH
) -> None:
    """Insert a new email verification token row for a user."""
    try:
        with get_connection(db_path) as connection:
            connection.execute(
                """
                INSERT INTO email_verification_tokens (user_id, token_hash, expires_at, used_at)
                VALUES (?, ?, ?, NULL)
                """,
                (user_id, token_hash, expires_at),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to create email verification token in {db_path}") from error


def get_email_verification_token(token_hash: str, db_path: Path = DB_PATH) -> dict | None:
    """Look up an unexpired, unused email verification token by its hash."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                """
                SELECT id, user_id, expires_at FROM email_verification_tokens
                WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?
                """,
                (token_hash, now),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load email verification token from {db_path}") from error

    return dict(row) if row is not None else None


def mark_email_verification_token_used(token_id: int, db_path: Path = DB_PATH) -> None:
    """Mark an email verification token as used, so it can't be redeemed again."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "UPDATE email_verification_tokens SET used_at = ? WHERE id = ?",
                (now, token_id),
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to mark email verification token {token_id} used in {db_path}"
        ) from error


def mark_email_verified(user_id: int, db_path: Path = DB_PATH) -> User:
    """Set a user's email_verified_at to now."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "UPDATE users SET email_verified_at = ?, updated_at = ? WHERE id = ?",
                (now, now, user_id),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to mark email verified for user {user_id} in {db_path}") from error

    updated_user = get_user_by_id(user_id, db_path)
    if updated_user is None:
        raise PersistenceError(f"Failed to reload updated user {user_id} in {db_path}")
    return updated_user


def record_email_verification_request(user_id: int, db_path: Path = DB_PATH) -> None:
    """Record one resend-verification request for a user."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "INSERT INTO email_verification_requests (user_id, requested_at) VALUES (?, ?)",
                (user_id, now),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to record email verification request in {db_path}") from error


def count_recent_email_verification_requests(
    user_id: int, window_minutes: int, db_path: Path = DB_PATH
) -> int:
    """Count a user's resend-verification requests within the trailing window."""
    since = (datetime.now(timezone.utc) - timedelta(minutes=window_minutes)).isoformat()

    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count FROM email_verification_requests
                WHERE user_id = ? AND requested_at > ?
                """,
                (user_id, since),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to count email verification requests in {db_path}") from error

    return int(row["count"])


def create_refresh_token(
    user_id: int,
    token_hash: str,
    issued_at: str,
    expires_at: str,
    db_path: Path = DB_PATH,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
    auth_time: str | None = None,
) -> None:
    """Insert a new refresh token row for a user.

    auth_time defaults to issued_at when omitted -- same fallback the
    startup migration backfill uses for pre-existing rows (see
    _ensure_refresh_token_metadata_columns in src/core/db.py), so callers
    that don't care about step-up freshness (most repository-level tests)
    don't need to pass it explicitly.
    """
    try:
        with get_connection(db_path) as connection:
            connection.execute(
                """
                INSERT INTO refresh_tokens
                    (user_id, token_hash, issued_at, expires_at, revoked_at, user_agent, ip_address, auth_time)
                VALUES (?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                (user_id, token_hash, issued_at, expires_at, user_agent, ip_address, auth_time or issued_at),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to create refresh token in {db_path}") from error


def get_refresh_token(token_hash: str, db_path: Path = DB_PATH) -> dict | None:
    """Look up a refresh token by its hash, regardless of whether it's revoked
    or expired -- returns None only if the hash was never issued at all.

    Returns a plain dict (id, user_id, expires_at, revoked_at, auth_time)
    rather than a domain model, since this row has no dataclass of its own.
    Callers must check `revoked_at`/`expires_at` themselves to determine
    whether the token is currently usable -- intentionally not filtered in
    SQL, because refresh_session()'s reuse detection needs to distinguish
    "this token was already used and rotated out" (a real theft signal)
    from "this token never existed," and a query that only ever returns
    unrevoked rows can't tell those apart.
    """
    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                "SELECT id, user_id, expires_at, revoked_at, auth_time FROM refresh_tokens WHERE token_hash = ?",
                (token_hash,),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load refresh token from {db_path}") from error

    return dict(row) if row is not None else None


def update_refresh_token_auth_time(token_hash: str, auth_time: str, db_path: Path = DB_PATH) -> None:
    """Update a refresh token's stored auth_time -- called by reauth() so the
    freshened value carries forward into the *next* rotation instead of
    reverting to the session's original login auth_time."""
    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "UPDATE refresh_tokens SET auth_time = ? WHERE token_hash = ?",
                (auth_time, token_hash),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to update refresh token auth_time in {db_path}") from error


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


def revoke_refresh_token_by_id(session_id: int, user_id: int, db_path: Path = DB_PATH) -> bool:
    """Revoke one specific refresh token by its row id, scoped to the owning user.

    Returns whether a row was actually revoked -- False means the id either
    doesn't exist or belongs to a different user, which the caller should
    treat as "not found" rather than leaking which case it was.
    """
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            cursor = connection.execute(
                """
                UPDATE refresh_tokens SET revoked_at = ?
                WHERE id = ? AND user_id = ? AND revoked_at IS NULL
                """,
                (now, session_id, user_id),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to revoke refresh token {session_id} in {db_path}") from error

    return cursor.rowcount > 0


def list_active_refresh_tokens_for_user(user_id: int, db_path: Path = DB_PATH) -> list[dict]:
    """Return every currently-valid (unrevoked, unexpired) refresh token row
    for a user, newest first -- powers the self-service active-sessions list.
    """
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                """
                SELECT id, token_hash, issued_at, expires_at, user_agent, ip_address
                FROM refresh_tokens
                WHERE user_id = ? AND revoked_at IS NULL AND expires_at > ?
                ORDER BY issued_at DESC
                """,
                (user_id, now),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to list refresh tokens for user {user_id} in {db_path}") from error

    return [dict(row) for row in rows]


def revoke_all_refresh_tokens_for_user(user_id: int, db_path: Path = DB_PATH) -> None:
    """Revoke every unrevoked refresh token belonging to a user.

    Ends every session the user currently holds at once -- used by admin
    deactivation and explicit session revocation, unlike revoke_refresh_token()
    above which only ends the one session tied to a single known token.
    """
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "UPDATE refresh_tokens SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
                (now, user_id),
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to revoke refresh tokens for user {user_id} in {db_path}"
        ) from error

    logger.debug("Revoked all refresh tokens for user %d in %s", user_id, db_path)


def create_admin_audit_event(
    actor_user_id: int | None,
    action: str,
    *,
    target_type: str | None = None,
    target_id: str | None = None,
    reason: str | None = None,
    metadata: dict | None = None,
    db_path: Path = DB_PATH,
) -> None:
    """Record one admin audit event.

    actor_user_id is nullable: NULL means system/script-initiated (e.g. the
    initial SUPER_ADMIN bootstrap, which by definition has no acting admin
    yet); non-null means a real admin acting through the API. Audit rows are
    append-only -- no update/delete function exists for this table.
    """
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                """
                INSERT INTO admin_audit_events
                    (actor_user_id, action, target_type, target_id, reason,
                     request_id, ip_address, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?)
                """,
                (
                    actor_user_id,
                    action,
                    target_type,
                    target_id,
                    reason,
                    json.dumps(metadata or {}),
                    now,
                ),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to record admin audit event in {db_path}") from error

    logger.info("Admin audit event: %s (actor=%s, target=%s/%s)", action, actor_user_id, target_type, target_id)


def list_users(db_path: Path = DB_PATH) -> list[User]:
    """Return every user, active or not, ordered by id.

    Unlike list_active_users below (scoped to active accounts for the
    notification scheduler), this is for the admin console's user list --
    admins need to see deactivated accounts too.
    """
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(f"SELECT {_COLUMNS} FROM users ORDER BY id").fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load users from {db_path}") from error

    return [User.from_dict(dict(row)) for row in rows]


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
