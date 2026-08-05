import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pyotp

from src.core.config import (
    DB_PATH,
    EMAIL_VERIFICATION_RESEND_LOCKOUT_MAX_ATTEMPTS,
    EMAIL_VERIFICATION_RESEND_LOCKOUT_WINDOW_MINUTES,
    EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES,
    FRONTEND_BASE_URL,
    LOGIN_LOCKOUT_MAX_ATTEMPTS,
    LOGIN_LOCKOUT_WINDOW_MINUTES,
    PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS,
    PASSWORD_RESET_LOCKOUT_WINDOW_MINUTES,
    PASSWORD_RESET_TOKEN_EXPIRY_MINUTES,
    REFRESH_TOKEN_EXPIRY_DAYS,
)
from src.core.exceptions import (
    AuthenticationError,
    ExternalServiceError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from src.core.logging import get_logger
from src.core.security import create_access_token
from src.core.security import create_refresh_token as generate_refresh_token
from src.core.security import decrypt_secret, encrypt_secret, hash_password, verify_password
from src.financial.notifications.email_sender import send_notification_email
from src.financial.users.models import User
from src.financial.users.repository import (
    count_recent_email_verification_requests,
    count_recent_failed_attempts,
    count_recent_password_reset_requests,
    count_unused_recovery_codes,
    create_email_verification_token,
    create_password_reset_token,
    create_recovery_codes,
    create_refresh_token,
    create_user,
    disable_mfa as _disable_mfa_row,
    enable_mfa,
    get_email_verification_token,
    get_mfa_secret_encrypted,
    get_password_reset_token,
    get_refresh_token,
    get_unused_recovery_code,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    list_active_refresh_tokens_for_user,
    mark_email_verification_token_used,
    mark_email_verified,
    mark_password_reset_token_used,
    mark_recovery_code_used,
    record_email_verification_request,
    record_login_attempt,
    record_password_reset_request,
    revoke_all_refresh_tokens_for_user,
    revoke_refresh_token,
    revoke_refresh_token_by_id,
    set_mfa_secret,
    update_password_hash,
    update_refresh_token_auth_time,
    update_user,
)

logger = get_logger(__name__)

MIN_PASSWORD_LENGTH = 8
MFA_RECOVERY_CODE_COUNT = 10

_INVALID_CREDENTIALS_MESSAGE = "Invalid username or password."
_TOTP_CODE_PATTERN = re.compile(r"^\d{6}$")


def _hash_token(raw_token: str) -> str:
    """Hash a random token with SHA-256 for storage/lookup.

    Not Argon2 -- the token is already high-entropy and single-use (unlike a
    user-chosen password), so a fast hash is appropriate here; this is a
    lookup, not a password check.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


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

    try:
        send_verification_email(user, db_path)
    except ExternalServiceError:
        # Verification is soft -- it never blocks login or feature access
        # (see the email_verified property), so registration must still
        # succeed even if SMTP isn't configured or is temporarily down.
        # Contrast with resend_verification_email(), an explicit user
        # action where a delivery failure should surface as a real error.
        logger.warning(
            "Could not send verification email for user %d (%s) -- "
            "verification can be resent later.",
            user.id,
            user.username,
        )

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


def issue_session(
    user_id: int,
    username: str,
    db_path: Path = DB_PATH,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
    auth_time: datetime | None = None,
) -> tuple[str, str]:
    """Issue a new (access_token, refresh_token) pair for a user.

    Called from both /auth/login and /auth/refresh (via refresh_session
    below), so both paths create sessions the same way. user_agent/
    ip_address are stored on the refresh-token row purely for the
    self-service active-sessions list -- they play no role in validating
    the token itself.

    auth_time defaults to now (a fresh login) but refresh_session() passes
    through the session's original auth_time unchanged -- rotating the
    token doesn't re-verify a password, so it must not reset step-up
    freshness (see create_access_token()'s docstring).
    """
    issued_at = datetime.now(timezone.utc)
    resolved_auth_time = auth_time or issued_at
    access_token = create_access_token(
        user_id=user_id, username=username, auth_time=resolved_auth_time
    )

    raw_refresh_token = generate_refresh_token()
    expires_at = issued_at + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)
    create_refresh_token(
        user_id,
        _hash_token(raw_refresh_token),
        issued_at.isoformat(),
        expires_at.isoformat(),
        db_path,
        user_agent=user_agent,
        ip_address=ip_address,
        auth_time=resolved_auth_time.isoformat(),
    )

    return access_token, raw_refresh_token


def refresh_session(
    refresh_token: str,
    db_path: Path = DB_PATH,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, str]:
    """Validate a refresh token and issue a new (access_token, refresh_token) pair.

    Rotates the refresh token on every use (revokes the old one, issues a new
    one) rather than reusing it -- this way a leaked-and-reused refresh token
    stops working the instant the legitimate client rotates past it, instead
    of remaining valid indefinitely until its natural expiry.

    Reuse detection: a legitimate client only ever holds the single latest,
    unrevoked token after each rotation. If the presented token hash matches
    a row that's already revoked, that's a real theft signal (someone is
    presenting a token that was already rotated out from under them) --
    every active session for this user is revoked defensively, not just
    this one request rejected.
    """
    token_hash = _hash_token(refresh_token)
    token_row = get_refresh_token(token_hash, db_path)

    if token_row is None:
        raise AuthenticationError("Invalid or expired refresh token.")

    if token_row["revoked_at"] is not None:
        logger.warning(
            "Refresh token reuse detected for user %d -- revoking all sessions.",
            token_row["user_id"],
        )
        revoke_all_refresh_tokens_for_user(token_row["user_id"], db_path)
        _notify_reuse_detected(token_row["user_id"], db_path)
        raise AuthenticationError("Invalid or expired refresh token.")

    if token_row["expires_at"] <= datetime.now(timezone.utc).isoformat():
        raise AuthenticationError("Invalid or expired refresh token.")

    user = get_user(token_row["user_id"], db_path)
    revoke_refresh_token(token_hash, db_path)

    return issue_session(
        user.id,
        user.username,
        db_path,
        user_agent=user_agent,
        ip_address=ip_address,
        auth_time=datetime.fromisoformat(token_row["auth_time"]),
    )


def _notify_reuse_detected(user_id: int, db_path: Path) -> None:
    """Best-effort security alert after refresh-token reuse triggers a mass
    revoke -- soft-fails the same way registration's verification email
    does, since a notification-delivery failure must never surface as (or
    mask) the AuthenticationError the caller is about to raise."""
    try:
        user = get_user(user_id, db_path)
        send_notification_email(
            "Security alert: your sessions were logged out",
            "We detected a used session token being replayed on your account "
            "and logged out every active session as a precaution. If this "
            "wasn't you, change your password immediately.",
            to_email=user.email,
        )
    except (ExternalServiceError, NotFoundError):
        logger.warning("Could not send reuse-detection alert email for user %d", user_id)


def reauth(
    user_id: int,
    password: str,
    refresh_token: str | None = None,
    db_path: Path = DB_PATH,
) -> str:
    """Re-verify the current user's password and mint a fresh access token
    with a fresh auth_time, without rotating the refresh token/session.

    Powers step-up auth: the frontend calls this when a sensitive action is
    rejected with StepUpRequiredError, then retries the original action with
    the new access token. If refresh_token is provided (it always should be
    for a real browser session), the active session's stored auth_time is
    also updated so the *next* /auth/refresh carries the fresher value
    forward instead of reverting to this session's original login time.
    """
    user = get_user(user_id, db_path)

    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Current password is incorrect.")

    auth_time = datetime.now(timezone.utc)
    access_token = create_access_token(user_id=user.id, username=user.username, auth_time=auth_time)

    if refresh_token is not None:
        update_refresh_token_auth_time(_hash_token(refresh_token), auth_time.isoformat(), db_path)

    logger.info("Step-up reauth succeeded for user %d (%s)", user.id, user.username)

    return access_token


def notify_new_device_if_needed(
    user: User,
    user_agent: str | None,
    ip_address: str | None,
    db_path: Path = DB_PATH,
) -> None:
    """Send a "new sign-in" alert if this login's (user_agent, ip_address)
    doesn't match any of the user's other currently-active sessions.

    Must be called *before* the new session is created (see /auth/login),
    using the pre-login snapshot of active sessions -- not folded into
    issue_session() itself, since that's also called from refresh_session()
    where the just-rotated-out session would spuriously be missing from the
    "active" list on every single token rotation, false-positiving on every
    refresh instead of only on genuinely new devices.

    Skipped entirely when the user has no other active sessions at all
    (first-ever login), so registration doesn't immediately trigger a
    "new device" alert for the user's own first sign-in.
    """
    existing_sessions = list_active_refresh_tokens_for_user(user.id, db_path)
    if not existing_sessions:
        return

    known = any(
        session["user_agent"] == user_agent and session["ip_address"] == ip_address
        for session in existing_sessions
    )
    if known:
        return

    try:
        send_notification_email(
            "New sign-in to your account",
            f"A new sign-in was detected on your account from "
            f"{ip_address or 'an unknown location'} using "
            f"{user_agent or 'an unknown device'}. If this wasn't you, "
            "change your password and log out of all devices immediately.",
            to_email=user.email,
        )
    except ExternalServiceError:
        logger.warning("Could not send new-device alert email for user %d", user.id)


def logout(refresh_token: str, db_path: Path = DB_PATH) -> None:
    """Revoke a refresh token, ending that session server-side.

    Only the given refresh token's session ends -- other sessions (e.g. a
    different browser/device) are unaffected, matching this app's
    current-session-only logout scope. See logout_all_sessions() for
    ending every session at once.
    """
    revoke_refresh_token(_hash_token(refresh_token), db_path)


def list_sessions(
    user_id: int, current_refresh_token: str | None = None, db_path: Path = DB_PATH
) -> list[dict]:
    """Return the user's active sessions, flagging which one (if any) is the caller's own."""
    current_hash = _hash_token(current_refresh_token) if current_refresh_token else None

    return [
        {
            "id": session["id"],
            "issued_at": session["issued_at"],
            "expires_at": session["expires_at"],
            "user_agent": session["user_agent"],
            "ip_address": session["ip_address"],
            "is_current": session["token_hash"] == current_hash,
        }
        for session in list_active_refresh_tokens_for_user(user_id, db_path)
    ]


def revoke_session(user_id: int, session_id: int, db_path: Path = DB_PATH) -> None:
    """Revoke one of the user's own sessions by id, raising NotFoundError if it isn't theirs."""
    revoked = revoke_refresh_token_by_id(session_id, user_id, db_path)
    if not revoked:
        raise NotFoundError(f"No active session with ID {session_id} found.")


def logout_all_sessions(user_id: int, db_path: Path = DB_PATH) -> None:
    """Revoke every session for a user at once -- "log out all devices"."""
    revoke_all_refresh_tokens_for_user(user_id, db_path)

    try:
        user = get_user(user_id, db_path)
        send_notification_email(
            "You were logged out of all devices",
            "Every active session on your account was just logged out. If "
            "you didn't do this, change your password immediately.",
            to_email=user.email,
        )
    except ExternalServiceError:
        logger.warning("Could not send logout-all-sessions confirmation email for user %d", user_id)


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


def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    db_path: Path = DB_PATH,
) -> None:
    """Verify the current password and replace it with a new one."""
    user = get_user(user_id, db_path)

    if not verify_password(current_password, user.password_hash):
        raise AuthenticationError("Current password is incorrect.")

    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

    new_password_hash = hash_password(new_password)
    update_password_hash(user_id, new_password_hash, db_path)

    logger.info("Changed password for user %d (%s)", user.id, user.username)

    try:
        send_notification_email(
            "Your password was changed",
            "Your account password was just changed. If you didn't do this, "
            "reset your password immediately.",
            to_email=user.email,
        )
    except ExternalServiceError:
        logger.warning("Could not send password-changed confirmation email for user %d", user_id)


def get_user(user_id: int, db_path: Path = DB_PATH) -> User:
    """Return the user with the given id, or raise NotFoundError."""
    user = get_user_by_id(user_id, db_path)

    if user is None:
        raise NotFoundError(f"No user found with ID {user_id}.")

    return user


def request_password_reset(email: str, db_path: Path = DB_PATH) -> None:
    """Email a password reset link if the email matches a user, else do nothing.

    Always returns normally regardless of whether the email exists (matches
    the existing anti-enumeration convention from authenticate_user) -- the
    caller should show the same "if that email exists..." message either way.

    Raises RateLimitError once an email has PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS
    recent requests within PASSWORD_RESET_LOCKOUT_WINDOW_MINUTES -- keyed by
    the raw requested email (not user_id) and counted before the lookup below,
    the same way authenticate_user's login lockout works, so a 429 here never
    reveals whether the email is actually registered.
    """
    normalized_email = email.strip().lower()

    if (
        count_recent_password_reset_requests(
            normalized_email, PASSWORD_RESET_LOCKOUT_WINDOW_MINUTES, db_path
        )
        >= PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS
    ):
        raise RateLimitError(
            "Too many password reset requests. "
            f"Try again in {PASSWORD_RESET_LOCKOUT_WINDOW_MINUTES} minutes."
        )

    record_password_reset_request(normalized_email, db_path)
    user = get_user_by_email(normalized_email, db_path)

    if user is None:
        return

    raw_token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRY_MINUTES)
    ).isoformat()
    create_password_reset_token(user.id, _hash_token(raw_token), expires_at, db_path)

    reset_link = f"{FRONTEND_BASE_URL}/reset-password?token={raw_token}"
    send_notification_email(
        subject="Reset your password",
        body=(
            "A password reset was requested for your account. "
            f"Use the link below to choose a new password:\n\n{reset_link}\n\n"
            f"This link expires in {PASSWORD_RESET_TOKEN_EXPIRY_MINUTES} minutes. "
            "If you didn't request this, you can ignore this email."
        ),
        to_email=user.email,
    )

    logger.info("Sent password reset email for user %d (%s)", user.id, user.username)


def reset_password(token: str, new_password: str, db_path: Path = DB_PATH) -> None:
    """Consume a password reset token and set a new password."""
    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

    token_row = get_password_reset_token(_hash_token(token), db_path)
    if token_row is None:
        raise ValidationError("This password reset link is invalid or has expired.")

    new_password_hash = hash_password(new_password)
    update_password_hash(token_row["user_id"], new_password_hash, db_path)
    mark_password_reset_token_used(token_row["id"], db_path)

    logger.info("Reset password for user %d via reset token", token_row["user_id"])


def send_verification_email(user: User, db_path: Path = DB_PATH) -> None:
    """Email a fresh verification link for a user's account.

    Called right after registration, and again on demand via
    resend_verification_email() below. Raises ExternalServiceError if SMTP
    isn't configured or delivery fails (same as send_notification_email()
    always has) -- callers decide whether that should be fatal; see
    register_user()'s comment for why it isn't there.
    """
    raw_token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES)
    ).isoformat()
    create_email_verification_token(user.id, _hash_token(raw_token), expires_at, db_path)

    verify_link = f"{FRONTEND_BASE_URL}/verify-email?token={raw_token}"
    expiry_hours = EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES // 60
    send_notification_email(
        subject="Verify your email",
        body=(
            "Please verify your email address to confirm you own this account:\n\n"
            f"{verify_link}\n\n"
            f"This link expires in {expiry_hours} hours."
        ),
        to_email=user.email,
    )

    logger.info("Sent verification email for user %d (%s)", user.id, user.username)


def resend_verification_email(user_id: int, db_path: Path = DB_PATH) -> None:
    """Rate-limited resend of the verification email for an already-authenticated user.

    Unlike request_password_reset(), this is scoped by user_id, not a raw
    email string -- resend is an authenticated action (the caller already
    knows their own account), so there's no anti-enumeration reason to key
    the lockout by email instead.
    """
    user = get_user(user_id, db_path)

    if user.email_verified:
        raise ValidationError("This email address is already verified.")

    if (
        count_recent_email_verification_requests(
            user_id, EMAIL_VERIFICATION_RESEND_LOCKOUT_WINDOW_MINUTES, db_path
        )
        >= EMAIL_VERIFICATION_RESEND_LOCKOUT_MAX_ATTEMPTS
    ):
        raise RateLimitError(
            "Too many verification emails requested. "
            f"Try again in {EMAIL_VERIFICATION_RESEND_LOCKOUT_WINDOW_MINUTES} minutes."
        )

    record_email_verification_request(user_id, db_path)
    send_verification_email(user, db_path)


def verify_email(token: str, db_path: Path = DB_PATH) -> User:
    """Consume an email verification token and mark the account verified."""
    token_row = get_email_verification_token(_hash_token(token), db_path)
    if token_row is None:
        raise ValidationError("This verification link is invalid or has expired.")

    updated_user = mark_email_verified(token_row["user_id"], db_path)
    mark_email_verification_token_used(token_row["id"], db_path)

    logger.info("Verified email for user %d (%s)", updated_user.id, updated_user.username)
    return updated_user


def _generate_recovery_code() -> str:
    """Generate one recovery code, formatted XXXX-XXXX (8 uppercase hex
    chars) -- visually distinct from a 6-digit TOTP code so verify_mfa_code()
    can tell the two apart unambiguously."""
    raw = secrets.token_hex(4).upper()
    return f"{raw[:4]}-{raw[4:]}"


def _normalize_recovery_code(code: str) -> str:
    return code.strip().upper()


def begin_mfa_enrollment(user_id: int, db_path: Path = DB_PATH) -> tuple[str, str]:
    """Generate a new TOTP secret for a user and store it, unconfirmed (see
    set_mfa_secret()) -- MFA isn't enabled until confirm_mfa_enrollment()
    verifies a real code against it. Returns (secret, otpauth_uri): the
    otpauth_uri renders as a QR code client-side; the raw secret is the
    manual-entry fallback. Calling this again before confirming just
    regenerates -- a normal retry path during setup, not a special case.
    """
    user = get_user(user_id, db_path)
    secret = pyotp.random_base32()
    set_mfa_secret(user_id, encrypt_secret(secret), db_path)
    otpauth_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email, issuer_name="AI Expense Tracker"
    )

    logger.info("Started MFA enrollment for user %d (%s)", user.id, user.username)

    return secret, otpauth_uri


def confirm_mfa_enrollment(user_id: int, code: str, db_path: Path = DB_PATH) -> list[str]:
    """Verify a real code against the just-enrolled (unconfirmed) secret and,
    on success, enable MFA and generate MFA_RECOVERY_CODE_COUNT recovery
    codes -- the only time they're ever returned in plaintext by the API.
    Raises ValidationError if there's no enrollment in progress or the code
    is wrong (never enables MFA against an unproven secret).
    """
    encrypted_secret = get_mfa_secret_encrypted(user_id, db_path)
    if encrypted_secret is None:
        raise ValidationError("No MFA enrollment is in progress for this account.")

    secret = decrypt_secret(encrypted_secret)
    if not pyotp.TOTP(secret).verify(code.strip(), valid_window=1):
        raise ValidationError("Invalid authentication code.")

    user = enable_mfa(user_id, db_path)

    recovery_codes = [_generate_recovery_code() for _ in range(MFA_RECOVERY_CODE_COUNT)]
    create_recovery_codes(user_id, [_hash_token(c) for c in recovery_codes], db_path)

    logger.info("Enabled MFA for user %d (%s)", user.id, user.username)

    return recovery_codes


def regenerate_recovery_codes(user_id: int, db_path: Path = DB_PATH) -> list[str]:
    """Invalidate a user's existing recovery codes and generate a fresh set."""
    user = get_user(user_id, db_path)
    if not user.mfa_enabled:
        raise ValidationError("MFA is not enabled for this account.")

    recovery_codes = [_generate_recovery_code() for _ in range(MFA_RECOVERY_CODE_COUNT)]
    create_recovery_codes(user_id, [_hash_token(c) for c in recovery_codes], db_path)

    logger.info("Regenerated MFA recovery codes for user %d (%s)", user.id, user.username)

    return recovery_codes


def disable_mfa(user_id: int, db_path: Path = DB_PATH) -> None:
    """Disable MFA for a user, clearing their secret and every recovery code."""
    user = _disable_mfa_row(user_id, db_path)

    logger.info("Disabled MFA for user %d (%s)", user.id, user.username)


def _verify_mfa_code_raw(user_id: int, code: str, db_path: Path) -> bool:
    """The actual TOTP/recovery-code check, with no lockout bookkeeping --
    see verify_mfa_code() for the lockout-wrapped, login-facing version."""
    code = code.strip()

    if _TOTP_CODE_PATTERN.fullmatch(code):
        encrypted_secret = get_mfa_secret_encrypted(user_id, db_path)
        if encrypted_secret is None:
            return False
        secret = decrypt_secret(encrypted_secret)
        return pyotp.TOTP(secret).verify(code, valid_window=1)

    code_hash = _hash_token(_normalize_recovery_code(code))
    recovery_code_row = get_unused_recovery_code(user_id, code_hash, db_path)
    if recovery_code_row is None:
        return False

    mark_recovery_code_used(recovery_code_row["id"], db_path)
    return True


def verify_mfa_code(user_id: int, code: str, db_path: Path = DB_PATH) -> bool:
    """Verify a TOTP or recovery code during MFA login, applying the same
    lockout bookkeeping authenticate_user() uses for passwords (shared budget,
    keyed by username) -- a 6-digit TOTP space is practically brute-forceable
    without *some* lockout, and this app already has the exact mechanism.

    Raises RateLimitError if the account is already locked out from recent
    failures (password or MFA). Returns False (not an exception) for a wrong
    code, mirroring how a wrong password is handled one layer up.
    """
    user = get_user(user_id, db_path)

    if (
        count_recent_failed_attempts(user.username, LOGIN_LOCKOUT_WINDOW_MINUTES, db_path)
        >= LOGIN_LOCKOUT_MAX_ATTEMPTS
    ):
        raise RateLimitError(
            f"Too many failed login attempts. Try again in {LOGIN_LOCKOUT_WINDOW_MINUTES} minutes."
        )

    if _verify_mfa_code_raw(user_id, code, db_path):
        record_login_attempt(user.username, succeeded=True, db_path=db_path)
        return True

    record_login_attempt(user.username, succeeded=False, db_path=db_path)
    return False
