import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.core.config import (
    DB_PATH,
    FRONTEND_BASE_URL,
    LOGIN_LOCKOUT_MAX_ATTEMPTS,
    LOGIN_LOCKOUT_WINDOW_MINUTES,
    PASSWORD_RESET_TOKEN_EXPIRY_MINUTES,
    REFRESH_TOKEN_EXPIRY_DAYS,
)
from src.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from src.core.logging import get_logger
from src.core.security import create_access_token
from src.core.security import create_refresh_token as generate_refresh_token
from src.core.security import hash_password, verify_password
from src.financial.notifications.email_sender import send_notification_email
from src.financial.users.models import User
from src.financial.users.repository import (
    count_recent_failed_attempts,
    create_password_reset_token,
    create_refresh_token,
    create_user,
    get_password_reset_token,
    get_refresh_token,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    mark_password_reset_token_used,
    record_login_attempt,
    revoke_refresh_token,
    update_password_hash,
    update_user,
)

logger = get_logger(__name__)

MIN_PASSWORD_LENGTH = 8

_INVALID_CREDENTIALS_MESSAGE = "Invalid username or password."


def _hash_token(raw_token: str) -> str:
    """Hash a random token with SHA-256 for storage/lookup.

    Not Argon2 -- the token is already high-entropy and single-use (unlike a
    user-chosen password), so a fast hash is appropriate here; this is a
    lookup, not a password check.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def register_user(
    username: str,
    email: str,
    password: str,
    db_path: Path = DB_PATH,
) -> User:
    """Validate, hash, and persist a new user account."""
    normalized_username = username.strip().lower()
    normalized_email = email.strip().lower()

    if not normalized_username:
        raise ValidationError("Username cannot be empty.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

    password_hash = hash_password(password)
    user = create_user(normalized_username, normalized_email, password_hash, db_path)

    logger.info("Registered user %d (%s)", user.id, user.username)

    return user


def authenticate_user(
    username: str,
    password: str,
    db_path: Path = DB_PATH,
) -> User:
    """Verify credentials and return the matching user, or raise AuthenticationError.

    Raises RateLimitError instead of even checking the password once a username has
    LOGIN_LOCKOUT_MAX_ATTEMPTS recent failures within LOGIN_LOCKOUT_WINDOW_MINUTES —
    keyed by the raw attempted username (not user_id), since a brute-force attempt
    can target a username that doesn't exist at all.
    """
    normalized_username = username.strip().lower()

    if (
        count_recent_failed_attempts(normalized_username, LOGIN_LOCKOUT_WINDOW_MINUTES, db_path)
        >= LOGIN_LOCKOUT_MAX_ATTEMPTS
    ):
        raise RateLimitError(
            f"Too many failed login attempts. Try again in {LOGIN_LOCKOUT_WINDOW_MINUTES} minutes."
        )

    user = get_user_by_username(normalized_username, db_path)

    if user is None or not verify_password(password, user.password_hash):
        record_login_attempt(normalized_username, succeeded=False, db_path=db_path)
        raise AuthenticationError(_INVALID_CREDENTIALS_MESSAGE)

    if not user.is_active:
        record_login_attempt(normalized_username, succeeded=False, db_path=db_path)
        raise AuthenticationError("This account has been deactivated.")

    record_login_attempt(normalized_username, succeeded=True, db_path=db_path)
    logger.info("Authenticated user %d (%s)", user.id, user.username)

    return user


def issue_session(user_id: int, username: str, db_path: Path = DB_PATH) -> tuple[str, str]:
    """Issue a new (access_token, refresh_token) pair for a user.

    Called from both /auth/login and /auth/refresh (via refresh_session
    below), so both paths create sessions the same way.
    """
    access_token = create_access_token(user_id=user_id, username=username)

    raw_refresh_token = generate_refresh_token()
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)
    create_refresh_token(
        user_id,
        _hash_token(raw_refresh_token),
        issued_at.isoformat(),
        expires_at.isoformat(),
        db_path,
    )

    return access_token, raw_refresh_token


def refresh_session(refresh_token: str, db_path: Path = DB_PATH) -> tuple[str, str]:
    """Validate a refresh token and issue a new (access_token, refresh_token) pair.

    Rotates the refresh token on every use (revokes the old one, issues a new
    one) rather than reusing it -- this way a leaked-and-reused refresh token
    stops working the instant the legitimate client rotates past it, instead
    of remaining valid indefinitely until its natural expiry.
    """
    token_hash = _hash_token(refresh_token)
    token_row = get_refresh_token(token_hash, db_path)

    if token_row is None:
        raise AuthenticationError("Invalid or expired refresh token.")

    user = get_user(token_row["user_id"], db_path)
    revoke_refresh_token(token_hash, db_path)

    return issue_session(user.id, user.username, db_path)


def logout(refresh_token: str, db_path: Path = DB_PATH) -> None:
    """Revoke a refresh token, ending that session server-side.

    Only the given refresh token's session ends -- other sessions (e.g. a
    different browser/device) are unaffected, matching this app's
    current-session-only logout scope.
    """
    revoke_refresh_token(_hash_token(refresh_token), db_path)


def update_profile(
    user_id: int,
    username: str | None = None,
    email: str | None = None,
    db_path: Path = DB_PATH,
) -> User:
    """Validate and persist a profile update (username and/or email)."""
    normalized_username = username.strip().lower() if username is not None else None
    normalized_email = email.strip().lower() if email is not None else None

    if normalized_username is not None and not normalized_username:
        raise ValidationError("Username cannot be empty.")

    if normalized_email is not None and not normalized_email:
        raise ValidationError("Email cannot be empty.")

    user = update_user(user_id, username=normalized_username, email=normalized_email, db_path=db_path)

    logger.info("Updated profile for user %d (%s)", user.id, user.username)

    return user


def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    db_path: Path = DB_PATH,
) -> None:
    """Verify the current password and replace it with a new one."""
    user = get_user(user_id, db_path)

    if not verify_password(current_password, user.password_hash):
        raise AuthenticationError("Current password is incorrect.")

    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

    new_password_hash = hash_password(new_password)
    update_password_hash(user_id, new_password_hash, db_path)

    logger.info("Changed password for user %d (%s)", user.id, user.username)


def get_user(user_id: int, db_path: Path = DB_PATH) -> User:
    """Return the user with the given id, or raise NotFoundError."""
    user = get_user_by_id(user_id, db_path)

    if user is None:
        raise NotFoundError(f"No user found with ID {user_id}.")

    return user


def request_password_reset(email: str, db_path: Path = DB_PATH) -> None:
    """Email a password reset link if the email matches a user, else do nothing.

    Always returns normally regardless of whether the email exists (matches
    the existing anti-enumeration convention from authenticate_user) -- the
    caller should show the same "if that email exists..." message either way.
    """
    normalized_email = email.strip().lower()
    user = get_user_by_email(normalized_email, db_path)

    if user is None:
        return

    raw_token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRY_MINUTES)
    ).isoformat()
    create_password_reset_token(user.id, _hash_token(raw_token), expires_at, db_path)

    reset_link = f"{FRONTEND_BASE_URL}/reset-password?token={raw_token}"
    send_notification_email(
        subject="Reset your password",
        body=(
            "A password reset was requested for your account. "
            f"Use the link below to choose a new password:\n\n{reset_link}\n\n"
            f"This link expires in {PASSWORD_RESET_TOKEN_EXPIRY_MINUTES} minutes. "
            "If you didn't request this, you can ignore this email."
        ),
        to_email=user.email,
    )

    logger.info("Sent password reset email for user %d (%s)", user.id, user.username)


def reset_password(token: str, new_password: str, db_path: Path = DB_PATH) -> None:
    """Consume a password reset token and set a new password."""
    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

    token_row = get_password_reset_token(_hash_token(token), db_path)
    if token_row is None:
        raise ValidationError("This password reset link is invalid or has expired.")

    new_password_hash = hash_password(new_password)
    update_password_hash(token_row["user_id"], new_password_hash, db_path)
    mark_password_reset_token_used(token_row["id"], db_path)

    logger.info("Reset password for user %d via reset token", token_row["user_id"])
