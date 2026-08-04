"""Tests for the users repository."""

import pytest

from src.core.exceptions import ValidationError
from src.financial.users.repository import (
    count_recent_failed_attempts,
    count_recent_password_reset_requests,
    create_admin_audit_event,
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
    record_password_reset_request,
    revoke_refresh_token,
    update_user,
    update_user_role,
)
from src.financial.users.role import PlatformRole


def test_create_user_returns_user_with_assigned_id(db_path) -> None:
    user = create_user("alice", "alice@example.com", "hashed-value", db_path)

    assert user.id > 0
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.password_hash == "hashed-value"
    assert user.is_active is True
    assert user.role == PlatformRole.USER


def test_update_user_role_changes_role(db_path) -> None:
    user = create_user("alice", "alice@example.com", "hashed-value", db_path)

    updated = update_user_role(user.id, PlatformRole.ADMIN, db_path)

    assert updated.role == PlatformRole.ADMIN

    reloaded = get_user_by_id(user.id, db_path)
    assert reloaded is not None
    assert reloaded.role == PlatformRole.ADMIN


def test_update_user_role_does_not_affect_other_users(db_path) -> None:
    alice = create_user("alice", "alice@example.com", "hashed-value", db_path)
    bob = create_user("bob", "bob@example.com", "hashed-value", db_path)

    update_user_role(alice.id, PlatformRole.SUPER_ADMIN, db_path)

    reloaded_bob = get_user_by_id(bob.id, db_path)
    assert reloaded_bob is not None
    assert reloaded_bob.role == PlatformRole.USER


def test_create_admin_audit_event_does_not_raise(db_path) -> None:
    from src.core.db import get_connection

    create_admin_audit_event(
        actor_user_id=None,
        action="role.assign",
        target_type="user",
        target_id="1",
        reason="Bootstrap promotion.",
        metadata={"previous_role": "user", "new_role": "super_admin"},
        db_path=db_path,
    )

    with get_connection(db_path) as connection:
        row = connection.execute("SELECT * FROM admin_audit_events").fetchone()

    assert row["action"] == "role.assign"
    assert row["actor_user_id"] is None
    assert row["target_type"] == "user"
    assert row["target_id"] == "1"
    assert row["reason"] == "Bootstrap promotion."
    assert '"new_role": "super_admin"' in row["metadata"]


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


def test_get_user_by_email_found(db_path) -> None:
    created = create_user("alice", "alice@example.com", "hashed-value", db_path)

    found = get_user_by_email("alice@example.com", db_path)

    assert found is not None
    assert found.id == created.id


def test_get_user_by_email_not_found(db_path) -> None:
    assert get_user_by_email("nobody@example.com", db_path) is None


def test_password_reset_token_round_trip(db_path) -> None:
    from datetime import datetime, timedelta, timezone

    user = create_user("alice", "alice@example.com", "hashed-value", db_path)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

    create_password_reset_token(user.id, "a-token-hash", expires_at, db_path)

    found = get_password_reset_token("a-token-hash", db_path)
    assert found is not None
    assert found["user_id"] == user.id


def test_get_password_reset_token_returns_none_when_expired(db_path) -> None:
    from datetime import datetime, timedelta, timezone

    user = create_user("alice", "alice@example.com", "hashed-value", db_path)
    expired_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

    create_password_reset_token(user.id, "a-token-hash", expired_at, db_path)

    assert get_password_reset_token("a-token-hash", db_path) is None


def test_get_password_reset_token_returns_none_once_used(db_path) -> None:
    from datetime import datetime, timedelta, timezone

    user = create_user("alice", "alice@example.com", "hashed-value", db_path)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    create_password_reset_token(user.id, "a-token-hash", expires_at, db_path)

    token_row = get_password_reset_token("a-token-hash", db_path)
    assert token_row is not None

    mark_password_reset_token_used(token_row["id"], db_path)

    assert get_password_reset_token("a-token-hash", db_path) is None


def test_refresh_token_round_trip(db_path) -> None:
    from datetime import datetime, timedelta, timezone

    user = create_user("alice", "alice@example.com", "hashed-value", db_path)
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(days=30)).isoformat()

    create_refresh_token(user.id, "a-token-hash", now.isoformat(), expires_at, db_path)

    found = get_refresh_token("a-token-hash", db_path)
    assert found is not None
    assert found["user_id"] == user.id


def test_get_refresh_token_returns_none_when_expired(db_path) -> None:
    from datetime import datetime, timedelta, timezone

    user = create_user("alice", "alice@example.com", "hashed-value", db_path)
    now = datetime.now(timezone.utc)
    expired_at = (now - timedelta(days=1)).isoformat()

    create_refresh_token(user.id, "a-token-hash", now.isoformat(), expired_at, db_path)

    assert get_refresh_token("a-token-hash", db_path) is None


def test_get_refresh_token_returns_none_once_revoked(db_path) -> None:
    from datetime import datetime, timedelta, timezone

    user = create_user("alice", "alice@example.com", "hashed-value", db_path)
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(days=30)).isoformat()
    create_refresh_token(user.id, "a-token-hash", now.isoformat(), expires_at, db_path)

    revoke_refresh_token("a-token-hash", db_path)

    assert get_refresh_token("a-token-hash", db_path) is None


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


def test_count_recent_password_reset_requests_counts_requests(db_path) -> None:
    record_password_reset_request("alice@example.com", db_path=db_path)
    record_password_reset_request("alice@example.com", db_path=db_path)

    assert count_recent_password_reset_requests("alice@example.com", 60, db_path) == 2


def test_count_recent_password_reset_requests_is_scoped_to_email(db_path) -> None:
    record_password_reset_request("alice@example.com", db_path=db_path)
    record_password_reset_request("bob@example.com", db_path=db_path)

    assert count_recent_password_reset_requests("alice@example.com", 60, db_path) == 1


def test_count_recent_password_reset_requests_ignores_requests_outside_window(db_path) -> None:
    from datetime import datetime, timedelta, timezone

    from src.core.db import get_connection

    stale_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=90)).isoformat()

    with get_connection(db_path) as connection:
        connection.execute(
            "INSERT INTO password_reset_requests (email, requested_at) VALUES (?, ?)",
            ("alice@example.com", stale_timestamp),
        )

    assert count_recent_password_reset_requests("alice@example.com", 60, db_path) == 0
