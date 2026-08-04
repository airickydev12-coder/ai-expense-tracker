"""Tests for the admin-only user-management service."""

from datetime import datetime, timedelta, timezone

import pytest

from src.core.db import get_connection
from src.core.exceptions import NotFoundError, ValidationError
from src.financial.users import admin_service
from src.financial.users.models import User
from src.financial.users.repository import create_refresh_token, get_refresh_token
from src.financial.users.role import PlatformRole
from src.financial.users.service import register_user


def _register(username: str, db_path) -> User:
    return register_user(username, f"{username}@example.com", "correct-password", db_path)


def test_list_users_returns_every_registered_user(db_path) -> None:
    alice = _register("alice", db_path)
    bob = _register("bob", db_path)

    users = admin_service.list_users(db_path)

    assert [user.id for user in users] == [alice.id, bob.id]


def test_get_user_detail_returns_matching_user(db_path) -> None:
    alice = _register("alice", db_path)

    found = admin_service.get_user_detail(alice.id, db_path)

    assert found.id == alice.id


def test_get_user_detail_raises_not_found_for_unknown_id(db_path) -> None:
    with pytest.raises(NotFoundError):
        admin_service.get_user_detail(999, db_path)


def test_set_user_active_status_deactivates_target(db_path) -> None:
    admin = _register("admin", db_path)
    alice = _register("alice", db_path)

    updated = admin_service.set_user_active_status(admin, alice.id, False, db_path)

    assert updated.is_active is False


def test_set_user_active_status_revokes_sessions_on_deactivation(db_path) -> None:
    admin = _register("admin", db_path)
    alice = _register("alice", db_path)
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(days=30)).isoformat()
    create_refresh_token(alice.id, "alice-token-hash", now.isoformat(), expires_at, db_path)

    admin_service.set_user_active_status(admin, alice.id, False, db_path)

    token_row = get_refresh_token("alice-token-hash", db_path)
    assert token_row is not None
    assert token_row["revoked_at"] is not None


def test_set_user_active_status_reactivation_does_not_touch_sessions(db_path) -> None:
    admin = _register("admin", db_path)
    alice = _register("alice", db_path)
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(days=30)).isoformat()
    create_refresh_token(alice.id, "alice-token-hash", now.isoformat(), expires_at, db_path)

    admin_service.set_user_active_status(admin, alice.id, True, db_path)

    assert get_refresh_token("alice-token-hash", db_path) is not None


def test_set_user_active_status_rejects_self_deactivation(db_path) -> None:
    admin = _register("admin", db_path)

    with pytest.raises(ValidationError):
        admin_service.set_user_active_status(admin, admin.id, False, db_path)


def test_set_user_active_status_records_audit_event(db_path) -> None:
    admin = _register("admin", db_path)
    alice = _register("alice", db_path)

    admin_service.set_user_active_status(admin, alice.id, False, db_path)

    with get_connection(db_path) as connection:
        row = connection.execute("SELECT * FROM admin_audit_events").fetchone()

    assert row["actor_user_id"] == admin.id
    assert row["action"] == "user.deactivate"
    assert row["target_id"] == str(alice.id)


def test_assign_role_changes_target_role(db_path) -> None:
    admin = _register("admin", db_path)
    alice = _register("alice", db_path)

    updated = admin_service.assign_role(admin, alice.id, PlatformRole.ADMIN, db_path)

    assert updated.role == PlatformRole.ADMIN


def test_assign_role_rejects_self_role_change(db_path) -> None:
    admin = _register("admin", db_path)

    with pytest.raises(ValidationError):
        admin_service.assign_role(admin, admin.id, PlatformRole.SUPER_ADMIN, db_path)


def test_assign_role_records_audit_event(db_path) -> None:
    admin = _register("admin", db_path)
    alice = _register("alice", db_path)

    admin_service.assign_role(admin, alice.id, PlatformRole.ADMIN, db_path)

    with get_connection(db_path) as connection:
        row = connection.execute("SELECT * FROM admin_audit_events").fetchone()

    assert row["actor_user_id"] == admin.id
    assert row["action"] == "role.assign"
    assert row["target_id"] == str(alice.id)
    assert '"new_role": "admin"' in row["metadata"]


def test_assign_role_raises_not_found_for_unknown_target(db_path) -> None:
    admin = _register("admin", db_path)

    with pytest.raises(NotFoundError):
        admin_service.assign_role(admin, 999, PlatformRole.ADMIN, db_path)


def test_revoke_user_sessions_revokes_every_refresh_token(db_path) -> None:
    admin = _register("admin", db_path)
    alice = _register("alice", db_path)
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(days=30)).isoformat()
    create_refresh_token(alice.id, "alice-token-hash", now.isoformat(), expires_at, db_path)

    admin_service.revoke_user_sessions(admin, alice.id, db_path)

    token_row = get_refresh_token("alice-token-hash", db_path)
    assert token_row is not None
    assert token_row["revoked_at"] is not None


def test_revoke_user_sessions_records_audit_event(db_path) -> None:
    admin = _register("admin", db_path)
    alice = _register("alice", db_path)

    admin_service.revoke_user_sessions(admin, alice.id, db_path)

    with get_connection(db_path) as connection:
        row = connection.execute("SELECT * FROM admin_audit_events").fetchone()

    assert row["actor_user_id"] == admin.id
    assert row["action"] == "session.revoke_all"
    assert row["target_id"] == str(alice.id)


def test_revoke_user_sessions_raises_not_found_for_unknown_target(db_path) -> None:
    admin = _register("admin", db_path)

    with pytest.raises(NotFoundError):
        admin_service.revoke_user_sessions(admin, 999, db_path)
