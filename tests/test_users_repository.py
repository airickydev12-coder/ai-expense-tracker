"""Tests for the users repository."""

import pytest

from src.core.exceptions import ValidationError
from src.financial.users.repository import (
    count_recent_failed_attempts,
    create_user,
    get_user_by_id,
    get_user_by_username,
    record_login_attempt,
    update_user,
)


def test_create_user_returns_user_with_assigned_id(db_path) -> None:
    user = create_user("alice", "alice@example.com", "hashed-value", db_path)

    assert user.id > 0
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.password_hash == "hashed-value"
    assert user.is_active is True


def test_create_user_duplicate_username_raises_validation_error(db_path) -> None:
    create_user("alice", "alice@example.com", "hashed-value", db_path)

    with pytest.raises(ValidationError):
        create_user("alice", "someone-else@example.com", "hashed-value", db_path)


def test_create_user_duplicate_email_raises_validation_error(db_path) -> None:
    create_user("alice", "alice@example.com", "hashed-value", db_path)

    with pytest.raises(ValidationError):
        create_user("someone-else", "alice@example.com", "hashed-value", db_path)


def test_get_user_by_username_found(db_path) -> None:
    created = create_user("alice", "alice@example.com", "hashed-value", db_path)

    found = get_user_by_username("alice", db_path)

    assert found is not None
    assert found.id == created.id


def test_get_user_by_username_not_found(db_path) -> None:
    assert get_user_by_username("nobody", db_path) is None


def test_get_user_by_id_found(db_path) -> None:
    created = create_user("alice", "alice@example.com", "hashed-value", db_path)

    found = get_user_by_id(created.id, db_path)

    assert found is not None
    assert found.username == "alice"


def test_get_user_by_id_not_found(db_path) -> None:
    assert get_user_by_id(999, db_path) is None


def test_update_user_updates_username_and_email(db_path) -> None:
    created = create_user("alice", "alice@example.com", "hashed-value", db_path)

    updated = update_user(created.id, username="alice2", email="alice2@example.com", db_path=db_path)

    assert updated.username == "alice2"
    assert updated.email == "alice2@example.com"


def test_update_user_updates_only_the_given_field(db_path) -> None:
    created = create_user("alice", "alice@example.com", "hashed-value", db_path)

    updated = update_user(created.id, username="alice2", db_path=db_path)

    assert updated.username == "alice2"
    assert updated.email == "alice@example.com"


def test_update_user_duplicate_username_raises_validation_error(db_path) -> None:
    create_user("alice", "alice@example.com", "hashed-value", db_path)
    bob = create_user("bob", "bob@example.com", "hashed-value", db_path)

    with pytest.raises(ValidationError):
        update_user(bob.id, username="alice", db_path=db_path)


def test_count_recent_failed_attempts_counts_only_failures(db_path) -> None:
    record_login_attempt("alice", succeeded=False, db_path=db_path)
    record_login_attempt("alice", succeeded=False, db_path=db_path)
    record_login_attempt("alice", succeeded=True, db_path=db_path)

    assert count_recent_failed_attempts("alice", 15, db_path) == 2


def test_count_recent_failed_attempts_is_scoped_to_username(db_path) -> None:
    record_login_attempt("alice", succeeded=False, db_path=db_path)
    record_login_attempt("bob", succeeded=False, db_path=db_path)

    assert count_recent_failed_attempts("alice", 15, db_path) == 1


def test_count_recent_failed_attempts_ignores_attempts_outside_window(db_path) -> None:
    from datetime import datetime, timedelta, timezone

    from src.core.db import get_connection

    stale_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()

    with get_connection(db_path) as connection:
        connection.execute(
            "INSERT INTO login_attempts (username, attempted_at, succeeded) VALUES (?, ?, 0)",
            ("alice", stale_timestamp),
        )

    assert count_recent_failed_attempts("alice", 15, db_path) == 0
