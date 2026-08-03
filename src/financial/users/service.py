from pathlib import Path

from src.core.config import DB_PATH
from src.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from src.core.logging import get_logger
from src.core.security import hash_password, verify_password
from src.financial.users.models import User
from src.financial.users.repository import (
    create_user,
    get_user_by_id,
    get_user_by_username,
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
    """Verify credentials and return the matching user, or raise AuthenticationError."""
    normalized_username = username.strip().lower()
    user = get_user_by_username(normalized_username, db_path)

    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError(_INVALID_CREDENTIALS_MESSAGE)

    if not user.is_active:
        raise AuthenticationError("This account has been deactivated.")

    logger.info("Authenticated user %d (%s)", user.id, user.username)

    return user


def get_user(user_id: int, db_path: Path = DB_PATH) -> User:
    """Return the user with the given id, or raise NotFoundError."""
    user = get_user_by_id(user_id, db_path)

    if user is None:
        raise NotFoundError(f"No user found with ID {user_id}.")

    return user
