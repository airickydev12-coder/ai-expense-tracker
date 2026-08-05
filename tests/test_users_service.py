"""Tests for the users service."""

import pytest

from src.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
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


def test_request_password_reset_locks_out_after_max_requests(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.core.config import PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS

    register_user("alice", "alice@example.com", "correct-password", db_path)
    monkeypatch.setattr(
        user_service, "send_notification_email", lambda subject, body, to_email=None: None
    )

    for _ in range(PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS):
        request_password_reset("alice@example.com", db_path)

    with pytest.raises(RateLimitError):
        request_password_reset("alice@example.com", db_path)


def test_request_password_reset_lockout_applies_to_unknown_emails(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.core.config import PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS

    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: pytest.fail(
            "Should not send an email for an unknown address"
        ),
    )

    for _ in range(PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS):
        request_password_reset("nobody@example.com", db_path)

    with pytest.raises(RateLimitError):
        request_password_reset("nobody@example.com", db_path)


def test_request_password_reset_lockout_is_scoped_to_email(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.core.config import PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS

    register_user("alice", "alice@example.com", "correct-password", db_path)
    register_user("bob", "bob@example.com", "correct-password", db_path)
    monkeypatch.setattr(
        user_service, "send_notification_email", lambda subject, body, to_email=None: None
    )

    for _ in range(PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS):
        request_password_reset("alice@example.com", db_path)

    # Bob isn't locked out by Alice's requests.
    request_password_reset("bob@example.com", db_path)


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


def test_register_user_sends_a_verification_email(db_path, monkeypatch: pytest.MonkeyPatch) -> None:
    sent: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: sent.update(subject=subject, body=body, to_email=to_email),
    )

    user = register_user("alice", "alice@example.com", "correct-password", db_path)

    assert sent["to_email"] == "alice@example.com"
    assert "verify-email?token=" in sent["body"]
    assert user.email_verified is False


def test_register_user_succeeds_even_if_the_verification_email_fails(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.core.exceptions import ExternalServiceError

    def _raise_external_service_error(*args: object, **kwargs: object) -> None:
        raise ExternalServiceError("SMTP is down")

    monkeypatch.setattr(user_service, "send_notification_email", _raise_external_service_error)

    user = register_user("alice", "alice@example.com", "correct-password", db_path)

    assert user.username == "alice"
    assert user.email_verified is False


def test_verify_email_success(db_path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: captured.update(body=body),
    )
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    assert registered.email_verified is False
    token = captured["body"].split("verify-email?token=")[1].split("\n")[0]

    verified_user = user_service.verify_email(token, db_path)

    assert verified_user.email_verified is True


def test_verify_email_rejects_invalid_token(db_path) -> None:
    with pytest.raises(ValidationError):
        user_service.verify_email("not-a-real-token", db_path)


def test_verify_email_token_is_single_use(db_path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: captured.update(body=body),
    )
    register_user("alice", "alice@example.com", "correct-password", db_path)
    token = captured["body"].split("verify-email?token=")[1].split("\n")[0]
    user_service.verify_email(token, db_path)

    with pytest.raises(ValidationError):
        user_service.verify_email(token, db_path)


def test_resend_verification_email_sends_a_new_token(db_path, monkeypatch: pytest.MonkeyPatch) -> None:
    sent_count = {"n": 0}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: sent_count.__setitem__("n", sent_count["n"] + 1),
    )
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    assert sent_count["n"] == 1

    user_service.resend_verification_email(registered.id, db_path)

    assert sent_count["n"] == 2


def test_resend_verification_email_rejects_already_verified(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: captured.update(body=body),
    )
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    token = captured["body"].split("verify-email?token=")[1].split("\n")[0]
    user_service.verify_email(token, db_path)

    with pytest.raises(ValidationError):
        user_service.resend_verification_email(registered.id, db_path)


def test_resend_verification_email_locks_out_after_max_attempts(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.core.config import EMAIL_VERIFICATION_RESEND_LOCKOUT_MAX_ATTEMPTS

    monkeypatch.setattr(
        user_service, "send_notification_email", lambda subject, body, to_email=None: None
    )
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    for _ in range(EMAIL_VERIFICATION_RESEND_LOCKOUT_MAX_ATTEMPTS):
        user_service.resend_verification_email(registered.id, db_path)

    with pytest.raises(RateLimitError):
        user_service.resend_verification_email(registered.id, db_path)


def test_refresh_session_detects_reuse_and_revokes_all_sessions(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    _, refresh_token_1 = issue_session(registered.id, registered.username, db_path=db_path)
    _, refresh_token_2 = issue_session(registered.id, registered.username, db_path=db_path)

    refresh_session(refresh_token_1, db_path=db_path)

    # Presenting the already-rotated token again is a reuse/theft signal.
    with pytest.raises(AuthenticationError):
        refresh_session(refresh_token_1, db_path=db_path)

    # The defensive revocation should also have killed the unrelated,
    # still-otherwise-valid second session.
    with pytest.raises(AuthenticationError):
        refresh_session(refresh_token_2, db_path=db_path)


def test_list_sessions_flags_the_current_session(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    _, token_1 = issue_session(
        registered.id, registered.username, db_path=db_path, user_agent="UA-1"
    )
    issue_session(registered.id, registered.username, db_path=db_path, user_agent="UA-2")

    sessions = user_service.list_sessions(registered.id, token_1, db_path)

    assert len(sessions) == 2
    current = [session for session in sessions if session["is_current"]]
    assert len(current) == 1
    assert current[0]["user_agent"] == "UA-1"


def test_list_sessions_with_no_current_token_flags_nothing(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    issue_session(registered.id, registered.username, db_path=db_path)

    sessions = user_service.list_sessions(registered.id, db_path=db_path)

    assert all(not session["is_current"] for session in sessions)


def test_revoke_session_ends_only_that_session(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    _, token_1 = issue_session(registered.id, registered.username, db_path=db_path)
    issue_session(registered.id, registered.username, db_path=db_path)
    session_id = user_service.list_sessions(registered.id, token_1, db_path)[0]["id"]

    user_service.revoke_session(registered.id, session_id, db_path)

    remaining = user_service.list_sessions(registered.id, db_path=db_path)
    assert len(remaining) == 1


def test_revoke_session_raises_not_found_for_another_users_session(db_path) -> None:
    alice = register_user("alice", "alice@example.com", "correct-password", db_path)
    bob = register_user("bob", "bob@example.com", "correct-password", db_path)
    issue_session(alice.id, alice.username, db_path=db_path)
    session_id = user_service.list_sessions(alice.id, db_path=db_path)[0]["id"]

    with pytest.raises(NotFoundError):
        user_service.revoke_session(bob.id, session_id, db_path)


def test_logout_all_sessions_revokes_every_session(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    issue_session(registered.id, registered.username, db_path=db_path)
    issue_session(registered.id, registered.username, db_path=db_path)

    user_service.logout_all_sessions(registered.id, db_path)

    assert user_service.list_sessions(registered.id, db_path=db_path) == []


def _auth_time_of(access_token: str):
    from datetime import datetime, timezone

    from src.core.security import decode_access_token

    payload = decode_access_token(access_token)
    return datetime.fromtimestamp(payload["auth_time"], tz=timezone.utc)


def test_issue_session_sets_a_fresh_auth_time(db_path) -> None:
    from datetime import datetime, timedelta, timezone

    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    before = datetime.now(timezone.utc)
    access_token, _ = issue_session(registered.id, registered.username, db_path=db_path)
    after = datetime.now(timezone.utc)

    # auth_time is encoded as a whole-second Unix timestamp (truncated, not
    # rounded), so it can read up to ~1s earlier than `before`.
    assert before - timedelta(seconds=1) <= _auth_time_of(access_token) <= after


def test_refresh_session_carries_auth_time_forward_unchanged(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    original_access_token, refresh_token = issue_session(
        registered.id, registered.username, db_path=db_path
    )

    new_access_token, _ = refresh_session(refresh_token, db_path=db_path)

    original_auth_time = _auth_time_of(original_access_token)
    new_auth_time = _auth_time_of(new_access_token)
    assert abs((new_auth_time - original_auth_time).total_seconds()) < 1


def test_reauth_success_returns_a_token_with_a_fresh_auth_time(db_path) -> None:
    from datetime import datetime, timedelta, timezone

    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    _, refresh_token = issue_session(registered.id, registered.username, db_path=db_path)

    before = datetime.now(timezone.utc)
    access_token = user_service.reauth(registered.id, "correct-password", refresh_token, db_path)
    after = datetime.now(timezone.utc)

    # auth_time is encoded as a whole-second Unix timestamp (truncated, not
    # rounded), so it can read up to ~1s earlier than `before`.
    assert before - timedelta(seconds=1) <= _auth_time_of(access_token) <= after


def test_reauth_rejects_wrong_password(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    with pytest.raises(AuthenticationError):
        user_service.reauth(registered.id, "wrong-password", None, db_path)


def test_reauth_updates_the_active_sessions_stored_auth_time(db_path) -> None:
    """A subsequent /auth/refresh must carry the *reauth-freshened* auth_time
    forward, not the session's original (now stale) login auth_time."""
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    _, refresh_token = issue_session(registered.id, registered.username, db_path=db_path)

    reauth_token = user_service.reauth(registered.id, "correct-password", refresh_token, db_path)
    refreshed_access_token, _ = refresh_session(refresh_token, db_path=db_path)

    reauth_auth_time = _auth_time_of(reauth_token)
    refreshed_auth_time = _auth_time_of(refreshed_access_token)
    assert abs((refreshed_auth_time - reauth_auth_time).total_seconds()) < 1


def test_notify_new_device_if_needed_skips_a_users_first_login(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: pytest.fail("Should not email on a first-ever login"),
    )

    user_service.notify_new_device_if_needed(registered, "UA-1", "1.2.3.4", db_path)


def test_notify_new_device_if_needed_sends_email_for_an_unrecognized_device(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    issue_session(registered.id, registered.username, db_path=db_path, user_agent="UA-1", ip_address="1.2.3.4")

    sent: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: sent.update(subject=subject, to_email=to_email),
    )

    user_service.notify_new_device_if_needed(registered, "UA-2", "5.6.7.8", db_path)

    assert sent["to_email"] == "alice@example.com"


def test_notify_new_device_if_needed_skips_a_recognized_device(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    issue_session(registered.id, registered.username, db_path=db_path, user_agent="UA-1", ip_address="1.2.3.4")

    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: pytest.fail("Should not email for a known device"),
    )

    user_service.notify_new_device_if_needed(registered, "UA-1", "1.2.3.4", db_path)


def test_refresh_session_reuse_sends_a_security_alert_email(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    _, refresh_token = issue_session(registered.id, registered.username, db_path=db_path)
    refresh_session(refresh_token, db_path=db_path)

    sent: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: sent.update(subject=subject, to_email=to_email),
    )

    with pytest.raises(AuthenticationError):
        refresh_session(refresh_token, db_path=db_path)

    assert sent["to_email"] == "alice@example.com"
    assert "logged out" in sent["subject"].lower()


def test_change_password_sends_a_confirmation_email(db_path, monkeypatch: pytest.MonkeyPatch) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    sent: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: sent.update(subject=subject, to_email=to_email),
    )

    change_password(registered.id, "correct-password", "new-password", db_path=db_path)

    assert sent["to_email"] == "alice@example.com"


def test_change_password_succeeds_even_if_the_confirmation_email_fails(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.core.exceptions import ExternalServiceError

    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    def _raise_external_service_error(subject, body, to_email=None):
        raise ExternalServiceError("SMTP is down")

    monkeypatch.setattr(user_service, "send_notification_email", _raise_external_service_error)

    change_password(registered.id, "correct-password", "new-password", db_path=db_path)

    authenticated = authenticate_user("alice", "new-password", db_path)
    assert authenticated.id == registered.id


def test_logout_all_sessions_sends_a_confirmation_email(
    db_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    issue_session(registered.id, registered.username, db_path=db_path)

    sent: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: sent.update(subject=subject, to_email=to_email),
    )

    user_service.logout_all_sessions(registered.id, db_path)

    assert sent["to_email"] == "alice@example.com"


def _totp_code_for(secret: str) -> str:
    import pyotp

    return pyotp.TOTP(secret).now()


def test_begin_mfa_enrollment_returns_a_secret_and_otpauth_uri(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    secret, otpauth_uri = user_service.begin_mfa_enrollment(registered.id, db_path)

    assert secret
    assert otpauth_uri.startswith("otpauth://totp/")
    assert "alice%40example.com" in otpauth_uri


def test_begin_mfa_enrollment_does_not_enable_mfa_yet(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    user_service.begin_mfa_enrollment(registered.id, db_path)

    assert get_user(registered.id, db_path).mfa_enabled is False


def test_confirm_mfa_enrollment_with_correct_code_enables_mfa(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    secret, _ = user_service.begin_mfa_enrollment(registered.id, db_path)

    recovery_codes = user_service.confirm_mfa_enrollment(
        registered.id, _totp_code_for(secret), db_path
    )

    assert get_user(registered.id, db_path).mfa_enabled is True
    assert len(recovery_codes) == user_service.MFA_RECOVERY_CODE_COUNT
    assert len(set(recovery_codes)) == user_service.MFA_RECOVERY_CODE_COUNT


def test_confirm_mfa_enrollment_rejects_a_wrong_code(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    user_service.begin_mfa_enrollment(registered.id, db_path)

    with pytest.raises(ValidationError):
        user_service.confirm_mfa_enrollment(registered.id, "000000", db_path)

    assert get_user(registered.id, db_path).mfa_enabled is False


def test_confirm_mfa_enrollment_rejects_when_no_enrollment_in_progress(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    with pytest.raises(ValidationError):
        user_service.confirm_mfa_enrollment(registered.id, "000000", db_path)


def test_verify_mfa_code_accepts_a_correct_totp_code(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    secret, _ = user_service.begin_mfa_enrollment(registered.id, db_path)
    user_service.confirm_mfa_enrollment(registered.id, _totp_code_for(secret), db_path)

    assert user_service.verify_mfa_code(registered.id, _totp_code_for(secret), db_path) is True


def test_verify_mfa_code_rejects_a_wrong_totp_code(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    secret, _ = user_service.begin_mfa_enrollment(registered.id, db_path)
    user_service.confirm_mfa_enrollment(registered.id, _totp_code_for(secret), db_path)

    assert user_service.verify_mfa_code(registered.id, "000000", db_path) is False


def test_verify_mfa_code_accepts_a_recovery_code_exactly_once(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    secret, _ = user_service.begin_mfa_enrollment(registered.id, db_path)
    recovery_codes = user_service.confirm_mfa_enrollment(
        registered.id, _totp_code_for(secret), db_path
    )

    assert user_service.verify_mfa_code(registered.id, recovery_codes[0], db_path) is True
    assert user_service.verify_mfa_code(registered.id, recovery_codes[0], db_path) is False


def test_verify_mfa_code_recovery_code_lookup_is_case_insensitive(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    secret, _ = user_service.begin_mfa_enrollment(registered.id, db_path)
    recovery_codes = user_service.confirm_mfa_enrollment(
        registered.id, _totp_code_for(secret), db_path
    )

    assert user_service.verify_mfa_code(registered.id, recovery_codes[0].lower(), db_path) is True


def test_verify_mfa_code_locks_out_after_max_failed_attempts(db_path) -> None:
    from src.core.config import LOGIN_LOCKOUT_MAX_ATTEMPTS

    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    secret, _ = user_service.begin_mfa_enrollment(registered.id, db_path)
    user_service.confirm_mfa_enrollment(registered.id, _totp_code_for(secret), db_path)

    for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
        user_service.verify_mfa_code(registered.id, "000000", db_path)

    with pytest.raises(RateLimitError):
        user_service.verify_mfa_code(registered.id, "000000", db_path)


def test_disable_mfa_clears_enrollment(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    secret, _ = user_service.begin_mfa_enrollment(registered.id, db_path)
    recovery_codes = user_service.confirm_mfa_enrollment(
        registered.id, _totp_code_for(secret), db_path
    )

    user_service.disable_mfa(registered.id, db_path)

    assert get_user(registered.id, db_path).mfa_enabled is False
    assert user_service.verify_mfa_code(registered.id, recovery_codes[0], db_path) is False


def test_regenerate_recovery_codes_invalidates_the_old_set(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)
    secret, _ = user_service.begin_mfa_enrollment(registered.id, db_path)
    old_codes = user_service.confirm_mfa_enrollment(registered.id, _totp_code_for(secret), db_path)

    new_codes = user_service.regenerate_recovery_codes(registered.id, db_path)

    assert set(new_codes).isdisjoint(old_codes)
    assert user_service.verify_mfa_code(registered.id, old_codes[0], db_path) is False
    assert user_service.verify_mfa_code(registered.id, new_codes[0], db_path) is True


def test_regenerate_recovery_codes_rejects_when_mfa_not_enabled(db_path) -> None:
    registered = register_user("alice", "alice@example.com", "correct-password", db_path)

    with pytest.raises(ValidationError):
        user_service.regenerate_recovery_codes(registered.id, db_path)
