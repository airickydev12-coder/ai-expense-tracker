"""Tests for the users service."""

import pytest

from src.core.exceptions import AuthenticationError, RateLimitError, ValidationError
from src.financial.users.service import authenticate_user, get_user, register_user


def test_register_user_normalizes_username_and_email_case(db_path) -> None:
    user = register_user("Alice", "ALICE@Example.com", "correct-password", db_path)

    assert user.username == "alice"
    assert user.email == "alice@example.com"


def test_register_user_rejects_empty_username(db_path) -> None:
    with pytest.raises(ValidationError):
        register_user("   ", "alice@example.com", "correct-password", db_path)


def test_register_user_rejects_short_password(db_path) -> None:
    with pytest.raises(ValidationError):
        register_user("alice", "alice@example.com", "short", db_path)


def test_register_user_duplicate_username_propagates_validation_error(db_path) -> None:
    register_user("alice", "alice@example.com", "correct-password", db_path)

    with pytest.raises(ValidationError):
        register_user("alice", "other@example.com", "correct-password", db_path)


def test_authenticate_user_success(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    authenticated = authenticate_user("alice", "correct-password", db_path)

    assert authenticated.id == registered.id


def test_authenticate_user_wrong_password_raises_authentication_error(db_path) -> None:
    register_user("alice", "alice@example.com", "correct-password", db_path)

    with pytest.raises(AuthenticationError) as wrong_password_error:
        authenticate_user("alice", "wrong-password", db_path)

    with pytest.raises(AuthenticationError) as nonexistent_user_error:
        authenticate_user("nobody", "correct-password", db_path)

    # Same message in both cases: don't leak whether the username exists.
    assert str(wrong_password_error.value) == str(nonexistent_user_error.value)


def test_authenticate_inactive_user_raises_authentication_error(db_path) -> None:
    from src.financial.users import repository as user_repository

    register_user("alice", "alice@example.com", "correct-password", db_path)
    user = user_repository.get_user_by_username("alice", db_path)
    assert user is not None

    from src.core.db import get_connection

    with get_connection(db_path) as connection:
        connection.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user.id,))

    with pytest.raises(AuthenticationError, match="deactivated"):
        authenticate_user("alice", "correct-password", db_path)


def test_get_user_returns_registered_user(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    fetched = get_user(registered.id, db_path)

    assert fetched.username == "alice"


def test_authenticate_user_locks_out_after_max_failed_attempts(db_path) -> None:
    from src.core.config import LOGIN_LOCKOUT_MAX_ATTEMPTS

    register_user("alice", "alice@example.com", "correct-password", db_path)

    for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
        with pytest.raises(AuthenticationError):
            authenticate_user("alice", "wrong-password", db_path)

    with pytest.raises(RateLimitError):
        authenticate_user("alice", "correct-password", db_path)


def test_authenticate_user_lockout_applies_to_nonexistent_usernames(db_path) -> None:
    from src.core.config import LOGIN_LOCKOUT_MAX_ATTEMPTS

    for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
        with pytest.raises(AuthenticationError):
            authenticate_user("nobody", "whatever", db_path)

    with pytest.raises(RateLimitError):
        authenticate_user("nobody", "whatever", db_path)


def test_authenticate_user_lockout_is_scoped_to_username(db_path) -> None:
    from src.core.config import LOGIN_LOCKOUT_MAX_ATTEMPTS

    register_user("alice", "alice@example.com", "correct-password", db_path)
    register_user("bob", "bob@example.com", "correct-password", db_path)

    for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
        with pytest.raises(AuthenticationError):
            authenticate_user("alice", "wrong-password", db_path)

    # Bob isn't locked out by Alice's failures.
    authenticated = authenticate_user("bob", "correct-password", db_path)
    assert authenticated.username == "bob"
