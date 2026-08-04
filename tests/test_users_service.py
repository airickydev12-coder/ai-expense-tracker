"""Tests for the users service."""

import pytest

from src.core.exceptions import AuthenticationError, RateLimitError, ValidationError
from src.financial.users import service as user_service
from src.financial.users.service import (
    authenticate_user,
    change_password,
    get_user,
    issue_session,
    logout,
    refresh_session,
    register_user,
    request_password_reset,
    reset_password,
    update_profile,
)


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


def test_update_profile_normalizes_username_and_email_case(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    updated = update_profile(registered.id, username="Alice2", email="ALICE2@Example.com", db_path=db_path)

    assert updated.username == "alice2"
    assert updated.email == "alice2@example.com"


def test_update_profile_rejects_blank_username(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    with pytest.raises(ValidationError):
        update_profile(registered.id, username="   ", db_path=db_path)


def test_change_password_success(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    change_password(registered.id, "correct-password", "new-password", db_path=db_path)

    authenticated = authenticate_user("alice", "new-password", db_path)
    assert authenticated.id == registered.id


def test_change_password_rejects_wrong_current_password(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    with pytest.raises(AuthenticationError):
        change_password(registered.id, "wrong-password", "new-password", db_path=db_path)


def test_change_password_rejects_short_new_password(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    with pytest.raises(ValidationError):
        change_password(registered.id, "correct-password", "short", db_path=db_path)


def test_request_password_reset_sends_email_for_known_address(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    register_user("alice", "alice@example.com", "correct-password", db_path)

    sent: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: sent.update(
            subject=subject, body=body, to_email=to_email
        ),
    )

    request_password_reset("alice@example.com", db_path)

    assert sent["to_email"] == "alice@example.com"
    assert "reset-password?token=" in sent["body"]


def test_request_password_reset_does_nothing_for_unknown_email(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: pytest.fail(
            "Should not send an email for an unknown address"
        ),
    )

    request_password_reset("nobody@example.com", db_path)


def test_reset_password_success(db_path, monkeypatch: pytest.MonkeyPatch) -> None:
    register_user("alice", "alice@example.com", "correct-password", db_path)

    captured_link: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: captured_link.update(body=body),
    )
    request_password_reset("alice@example.com", db_path)

    token = captured_link["body"].split("reset-password?token=")[1].split("\n")[0]

    reset_password(token, "new-password", db_path=db_path)

    authenticated = authenticate_user("alice", "new-password", db_path)
    assert authenticated.username == "alice"


def test_reset_password_rejects_invalid_token(db_path) -> None:
    with pytest.raises(ValidationError):
        reset_password("not-a-real-token", "new-password", db_path=db_path)


def test_reset_password_token_is_single_use(db_path, monkeypatch: pytest.MonkeyPatch) -> None:
    register_user("alice", "alice@example.com", "correct-password", db_path)

    captured_link: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: captured_link.update(body=body),
    )
    request_password_reset("alice@example.com", db_path)
    token = captured_link["body"].split("reset-password?token=")[1].split("\n")[0]

    reset_password(token, "new-password", db_path=db_path)

    with pytest.raises(ValidationError):
        reset_password(token, "another-password", db_path=db_path)


def test_reset_password_rejects_short_new_password(db_path, monkeypatch: pytest.MonkeyPatch) -> None:
    register_user("alice", "alice@example.com", "correct-password", db_path)

    captured_link: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: captured_link.update(body=body),
    )
    request_password_reset("alice@example.com", db_path)
    token = captured_link["body"].split("reset-password?token=")[1].split("\n")[0]

    with pytest.raises(ValidationError):
        reset_password(token, "short", db_path=db_path)


def test_issue_session_returns_access_and_refresh_tokens(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    access_token, refresh_token = issue_session(registered.id, registered.username, db_path=db_path)

    assert access_token
    assert refresh_token
    assert access_token != refresh_token


def test_refresh_session_issues_new_tokens(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    _, refresh_token = issue_session(registered.id, registered.username, db_path=db_path)

    new_access_token, new_refresh_token = refresh_session(refresh_token, db_path=db_path)

    assert new_access_token
    assert new_refresh_token
    assert new_refresh_token != refresh_token


def test_refresh_session_rotates_out_the_old_token(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    _, refresh_token = issue_session(registered.id, registered.username, db_path=db_path)

    refresh_session(refresh_token, db_path=db_path)

    with pytest.raises(AuthenticationError):
        refresh_session(refresh_token, db_path=db_path)


def test_refresh_session_rejects_unknown_token(db_path) -> None:
    with pytest.raises(AuthenticationError):
        refresh_session("not-a-real-refresh-token", db_path=db_path)


def test_logout_revokes_the_refresh_token(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    _, refresh_token = issue_session(registered.id, registered.username, db_path=db_path)

    logout(refresh_token, db_path=db_path)

    with pytest.raises(AuthenticationError):
        refresh_session(refresh_token, db_path=db_path)


def test_logout_does_not_affect_other_sessions(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    _, refresh_token_1 = issue_session(registered.id, registered.username, db_path=db_path)
    _, refresh_token_2 = issue_session(registered.id, registered.username, db_path=db_path)

    logout(refresh_token_1, db_path=db_path)

    # The other session's refresh token still works.
    new_access_token, _ = refresh_session(refresh_token_2, db_path=db_path)
    assert new_access_token


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
