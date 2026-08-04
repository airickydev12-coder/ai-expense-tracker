from pathlib import Path

from src.core.config import (
    DB_PATH,
    LOGIN_LOCKOUT_MAX_ATTEMPTS,
    LOGIN_LOCKOUT_WINDOW_MINUTES,
)
from src.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from src.core.logging import get_logger
from src.core.security import hash_password, verify_password
from src.financial.users.models import User
from src.financial.users.repository import (
    count_recent_failed_attempts,
    create_user,
    get_user_by_id,
    get_user_by_username,
    record_login_attempt,
    update_user,
)

logger = get_logger(__name__)

MIN_PASSWORD_LENGTH = 8

_INVALID_CREDENTIALS_MESSAGE = "Invalid username or password."


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


def get_user(user_id: int, db_path: Path = DB_PATH) -> User:
    """Return the user with the given id, or raise NotFoundError."""
    user = get_user_by_id(user_id, db_path)

    if user is None:
        raise NotFoundError(f"No user found with ID {user_id}.")

    return user
