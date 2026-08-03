"""Tests for the users repository."""

import pytest

from src.core.exceptions import ValidationError
from src.financial.users.repository import (
    create_user,
    get_user_by_id,
    get_user_by_username,
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
