"""Tests for the auth API endpoints."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.config import DB_PATH, JWT_ALGORITHM, JWT_SECRET_KEY, STEP_UP_MAX_AGE_MINUTES
from src.core.db import get_connection
from src.financial.users import service as user_service

client = TestClient(app)


def _stale_access_token(user_id: int, username: str = "alice") -> str:
    """Build a validly-signed, unexpired access token whose auth_time is
    older than STEP_UP_MAX_AGE_MINUTES -- simulates a long-lived session
    that hasn't re-authenticated recently, for step-up-required tests."""
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user_id),
            "username": username,
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "auth_time": int((now - timedelta(minutes=STEP_UP_MAX_AGE_MINUTES + 1)).timestamp()),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def setup_function() -> None:
    """Clear the shared client's cookie jar before every test.

    Without this, a refresh-token cookie set by one test's login would leak
    into the next test via TestClient's persistent cookie jar (it's one
    module-level `client`, reused across the whole file) -- each test should
    control its own cookie state explicitly instead.
    """
    client.cookies.clear()


def _register(username: str = "alice", password: str = "correct-password"):
    return client.post(
        "/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )


def _login(username: str = "alice", password: str = "correct-password"):
    return client.post("/auth/login", json={"username": username, "password": password})


def test_register_success() -> None:
    response = _register()

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert body["role"] == "user"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_username_returns_400() -> None:
    _register()

    response = _register()

    assert response.status_code == 400


def test_register_weak_password_returns_422() -> None:
    response = client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "short"},
    )

    # Pydantic schema validation (min_length=8) fails before our domain
    # ValidationError handler ever runs, so this is FastAPI's own 422 —
    # a distinct code path from the 400 duplicate-username case above.
    assert response.status_code == 422


def test_login_success() -> None:
    _register()

    response = _login()

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert "refresh_token" not in body

    refresh_cookie = client.cookies.get("refresh_token")
    assert refresh_cookie
    assert refresh_cookie != body["access_token"]

    set_cookie_header = response.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie_header
    assert "samesite=lax" in set_cookie_header
    # COOKIE_SECURE defaults to false for tests/local dev (the LAN
    # deployment is plain HTTP) -- a Secure cookie wouldn't even be sent
    # back over the test client's requests.
    assert "secure" not in set_cookie_header


def test_login_wrong_password_returns_401() -> None:
    _register()

    wrong_password_response = client.post(
        "/auth/login", json={"username": "alice", "password": "wrong-password"}
    )
    nonexistent_user_response = client.post(
        "/auth/login", json={"username": "nobody", "password": "correct-password"}
    )

    assert wrong_password_response.status_code == 401
    assert nonexistent_user_response.status_code == 401
    # Same message in both cases: don't leak whether the username exists.
    assert wrong_password_response.json()["detail"] == nonexistent_user_response.json()["detail"]


def test_me_with_valid_token() -> None:
    _register()
    token = _login().json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_me_without_authorization_header_returns_401() -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_with_malformed_token_returns_401() -> None:
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_me_with_deactivated_user_returns_401() -> None:
    _register()
    token = _login().json()["access_token"]
    user_id = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["id"]

    with get_connection(DB_PATH) as connection:
        connection.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_update_profile_success() -> None:
    _register()
    token = _login().json()["access_token"]

    response = client.patch(
        "/auth/me",
        json={"username": "alice2"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "alice2"


def test_update_profile_requires_at_least_one_field() -> None:
    _register()
    token = _login().json()["access_token"]

    response = client.patch(
        "/auth/me",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


def test_update_profile_duplicate_username_returns_400() -> None:
    _register("alice")
    _register("bob")
    token = _login("bob").json()["access_token"]

    response = client.patch(
        "/auth/me",
        json={"username": "alice"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


def test_update_profile_without_authorization_header_returns_401() -> None:
    response = client.patch("/auth/me", json={"username": "alice2"})

    assert response.status_code == 401


def test_change_password_success() -> None:
    _register()
    token = _login().json()["access_token"]

    response = client.post(
        "/auth/change-password",
        json={"current_password": "correct-password", "new_password": "new-password"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204

    new_login = client.post("/auth/login", json={"username": "alice", "password": "new-password"})
    assert new_login.status_code == 200


def test_change_password_rejects_wrong_current_password() -> None:
    _register()
    token = _login().json()["access_token"]

    response = client.post(
        "/auth/change-password",
        json={"current_password": "wrong-password", "new_password": "new-password"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_change_password_rejects_weak_new_password() -> None:
    _register()
    token = _login().json()["access_token"]

    response = client.post(
        "/auth/change-password",
        json={"current_password": "correct-password", "new_password": "short"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_change_password_without_authorization_header_returns_401() -> None:
    response = client.post(
        "/auth/change-password",
        json={"current_password": "correct-password", "new_password": "new-password"},
    )

    assert response.status_code == 401


def test_forgot_password_returns_202_for_known_email(monkeypatch: pytest.MonkeyPatch) -> None:
    _register()

    sent: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: sent.update(body=body),
    )

    response = client.post("/auth/forgot-password", json={"email": "alice@example.com"})

    assert response.status_code == 202
    assert "reset-password?token=" in sent["body"]


def test_forgot_password_returns_202_for_unknown_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: pytest.fail("Should not send for an unknown email"),
    )

    response = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})

    # Same 202 either way -- don't leak whether the email is registered.
    assert response.status_code == 202


def test_forgot_password_locks_out_after_max_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.core.config import PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS

    _register()
    monkeypatch.setattr(
        user_service, "send_notification_email", lambda subject, body, to_email=None: None
    )

    for _ in range(PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS):
        response = client.post("/auth/forgot-password", json={"email": "alice@example.com"})
        assert response.status_code == 202

    locked_out_response = client.post(
        "/auth/forgot-password", json={"email": "alice@example.com"}
    )

    assert locked_out_response.status_code == 429


def test_reset_password_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _register()

    sent: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: sent.update(body=body),
    )
    client.post("/auth/forgot-password", json={"email": "alice@example.com"})
    token = sent["body"].split("reset-password?token=")[1].split("\n")[0]

    response = client.post(
        "/auth/reset-password", json={"token": token, "new_password": "new-password"}
    )

    assert response.status_code == 204

    new_login = client.post("/auth/login", json={"username": "alice", "password": "new-password"})
    assert new_login.status_code == 200


def test_reset_password_rejects_invalid_token() -> None:
    response = client.post(
        "/auth/reset-password", json={"token": "not-a-real-token", "new_password": "new-password"}
    )

    assert response.status_code == 400


def test_refresh_success() -> None:
    _register()
    _login()
    old_refresh_token = client.cookies.get("refresh_token")

    response = client.post("/auth/refresh")

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert "refresh_token" not in body

    new_refresh_token = client.cookies.get("refresh_token")
    assert new_refresh_token
    assert new_refresh_token != old_refresh_token

    # The new access token is valid.
    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me_response.status_code == 200


def test_refresh_rejects_already_rotated_token() -> None:
    _register()
    _login()
    old_refresh_token = client.cookies.get("refresh_token")

    client.post("/auth/refresh")  # rotates -- old_refresh_token is now revoked

    client.cookies.set("refresh_token", old_refresh_token)
    reused_response = client.post("/auth/refresh")

    assert reused_response.status_code == 401


def test_refresh_rejects_unknown_token() -> None:
    client.cookies.set("refresh_token", "not-a-real-refresh-token")

    response = client.post("/auth/refresh")

    assert response.status_code == 401


def test_refresh_without_cookie_returns_401() -> None:
    response = client.post("/auth/refresh")

    assert response.status_code == 401


def test_logout_revokes_the_refresh_token() -> None:
    _register()
    _login()
    refresh_token = client.cookies.get("refresh_token")

    logout_response = client.post("/auth/logout")

    assert logout_response.status_code == 204
    assert client.cookies.get("refresh_token") is None

    # Re-present the (now revoked) token to confirm the session was ended
    # server-side, not just that the cookie was cleared client-side.
    client.cookies.set("refresh_token", refresh_token)
    refresh_response = client.post("/auth/refresh")
    assert refresh_response.status_code == 401


def test_logout_without_cookie_is_a_no_op() -> None:
    response = client.post("/auth/logout")

    assert response.status_code == 204


def test_login_locks_out_after_max_failed_attempts() -> None:
    from src.core.config import LOGIN_LOCKOUT_MAX_ATTEMPTS

    _register()

    for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
        response = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
        assert response.status_code == 401

    locked_out_response = client.post(
        "/auth/login", json={"username": "alice", "password": "correct-password"}
    )

    assert locked_out_response.status_code == 429


def test_me_with_expired_token_returns_401() -> None:
    now = datetime.now(timezone.utc)
    expired_token = jwt.encode(
        {
            "sub": "1",
            "username": "alice",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401


def test_register_response_includes_unverified_email_status() -> None:
    response = _register()

    assert response.json()["email_verified"] is False


def test_verify_email_success(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: captured.update(body=body),
    )
    _register()
    token = captured["body"].split("verify-email?token=")[1].split("\n")[0]

    response = client.post("/auth/verify-email", json={"token": token})

    assert response.status_code == 204

    me_response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {_login().json()['access_token']}"}
    )
    assert me_response.json()["email_verified"] is True


def test_verify_email_rejects_invalid_token() -> None:
    response = client.post("/auth/verify-email", json={"token": "not-a-real-token"})

    assert response.status_code == 400


def test_resend_verification_requires_authentication() -> None:
    response = client.post("/auth/resend-verification")

    assert response.status_code == 401


def test_resend_verification_success(monkeypatch: pytest.MonkeyPatch) -> None:
    sent_count = {"n": 0}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: sent_count.__setitem__("n", sent_count["n"] + 1),
    )
    _register()
    token = _login().json()["access_token"]
    assert sent_count["n"] == 1

    response = client.post(
        "/auth/resend-verification", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 202
    assert sent_count["n"] == 2


def test_resend_verification_rejects_already_verified(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        user_service,
        "send_notification_email",
        lambda subject, body, to_email=None: captured.update(body=body),
    )
    _register()
    token = captured["body"].split("verify-email?token=")[1].split("\n")[0]
    client.post("/auth/verify-email", json={"token": token})
    access_token = _login().json()["access_token"]

    response = client.post(
        "/auth/resend-verification", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 400


def test_list_sessions_returns_active_sessions() -> None:
    _register()
    access_token = _login().json()["access_token"]

    response = client.get("/auth/sessions", headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 1
    assert sessions[0]["is_current"] is True
    assert "id" in sessions[0]


def test_list_sessions_requires_authentication() -> None:
    response = client.get("/auth/sessions")

    assert response.status_code == 401


def test_revoke_session_ends_that_session() -> None:
    _register()
    access_token = _login().json()["access_token"]
    session_id = client.get(
        "/auth/sessions", headers={"Authorization": f"Bearer {access_token}"}
    ).json()[0]["id"]

    response = client.delete(
        f"/auth/sessions/{session_id}", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 204

    refresh_response = client.post("/auth/refresh")
    assert refresh_response.status_code == 401


def test_revoke_session_returns_404_for_unknown_id() -> None:
    _register()
    access_token = _login().json()["access_token"]

    response = client.delete(
        "/auth/sessions/999999", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 404


def test_revoke_all_sessions_ends_every_session_and_clears_the_cookie() -> None:
    _register()
    access_token = _login().json()["access_token"]
    # A second session/device for the same account.
    client.post("/auth/login", json={"username": "alice", "password": "correct-password"})
    refresh_token = client.cookies.get("refresh_token")

    response = client.post(
        "/auth/sessions/revoke-all", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 204
    assert client.cookies.get("refresh_token") is None

    client.cookies.set("refresh_token", refresh_token)
    refresh_response = client.post("/auth/refresh")
    assert refresh_response.status_code == 401


def test_revoke_all_sessions_requires_recent_auth() -> None:
    _register()
    access_token = _login().json()["access_token"]
    user_id = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"}).json()["id"]
    stale_token = _stale_access_token(user_id)

    response = client.post(
        "/auth/sessions/revoke-all", headers={"Authorization": f"Bearer {stale_token}"}
    )

    assert response.status_code == 403
    assert response.json()["code"] == "step_up_required"


def test_reauth_success_returns_a_fresh_access_token() -> None:
    _register()
    access_token = _login().json()["access_token"]

    response = client.post(
        "/auth/reauth",
        json={"password": "correct-password"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_reauth_rejects_the_wrong_password() -> None:
    _register()
    access_token = _login().json()["access_token"]

    response = client.post(
        "/auth/reauth",
        json={"password": "wrong-password"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 401


def test_reauth_requires_authentication() -> None:
    response = client.post("/auth/reauth", json={"password": "correct-password"})

    assert response.status_code == 401


def test_reauth_clears_the_step_up_requirement() -> None:
    _register()
    access_token = _login().json()["access_token"]
    user_id = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"}).json()["id"]
    stale_token = _stale_access_token(user_id)

    rejected = client.post(
        "/auth/sessions/revoke-all", headers={"Authorization": f"Bearer {stale_token}"}
    )
    assert rejected.status_code == 403

    reauth_response = client.post(
        "/auth/reauth",
        json={"password": "correct-password"},
        headers={"Authorization": f"Bearer {stale_token}"},
    )
    fresh_token = reauth_response.json()["access_token"]

    allowed = client.post(
        "/auth/sessions/revoke-all", headers={"Authorization": f"Bearer {fresh_token}"}
    )
    assert allowed.status_code == 204
