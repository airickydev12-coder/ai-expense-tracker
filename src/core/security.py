"""
Password hashing, JWT access-token, and symmetric-encryption helpers for the
Financial Core application.

Infrastructure-layer utilities (ADR-001): no domain or FastAPI concepts here,
just cryptographic primitives used by src/financial/users/service.py and
src/api/dependencies.py.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken

from src.core.config import (
    JWT_ALGORITHM,
    JWT_EXPIRY_MINUTES,
    JWT_SECRET_KEY,
    MFA_CHALLENGE_TOKEN_EXPIRY_MINUTES,
    MFA_ENCRYPTION_KEY,
)
from src.core.exceptions import AuthenticationError

_hasher = PasswordHasher()
_fernet = Fernet(MFA_ENCRYPTION_KEY)

_MFA_CHALLENGE_PURPOSE = "mfa_challenge"


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored Argon2 hash."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(
    user_id: int, username: str, auth_time: datetime | None = None
) -> str:
    """Issue a signed JWT access token for the given user.

    auth_time defaults to now (a fresh login) but callers that are rotating
    an existing session (see refresh_session()) pass through the original
    login's auth_time unchanged -- it marks when the password was last
    actually verified, which token rotation alone doesn't refresh. Sensitive
    endpoints use it (via require_recent_auth in src/api/dependencies.py) to
    require a recent-enough auth_time before allowing the action.

    auth_time is encoded as a Unix timestamp explicitly -- PyJWT only
    auto-converts its own reserved claims (iat/exp/nbf) from datetime; a
    custom claim like auth_time is left to json.dumps() as-is and raises
    TypeError if it's still a datetime.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRY_MINUTES),
        "auth_time": int((auth_time or now).timestamp()),
        "purpose": "access",
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token() -> str:
    """Generate a new high-entropy random refresh token.

    Unlike the JWT access token, this carries no payload of its own -- the
    caller looks up the (hashed) token server-side to resolve the session,
    which is what makes it revocable, unlike a self-contained JWT.
    """
    return secrets.token_urlsafe(32)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token, raising AuthenticationError if invalid.

    A pure signature/expiry primitive -- deliberately doesn't check the
    "purpose" claim itself (see create_access_token()). That check belongs to
    src/api/dependencies.py's get_current_user(), the FastAPI-facing trust
    boundary between an access token and other narrowly-scoped tokens (e.g.
    the MFA challenge token below) that also happen to be valid, signed JWTs.
    """
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as error:
        raise AuthenticationError("Token has expired.") from error
    except jwt.InvalidTokenError as error:
        raise AuthenticationError("Invalid authentication token.") from error


def create_mfa_challenge_token(user_id: int) -> str:
    """Issue a short-lived signed JWT proving a user has passed the first
    (password) factor of login and is now expected to present a TOTP or
    recovery code -- returned by POST /auth/login instead of real tokens
    when MFA is enabled, and consumed once by POST /auth/mfa/verify.

    Deliberately a separate token shape from create_access_token() (its own
    "purpose" value, no auth_time/username), not merely a differently-scoped
    access token -- this makes it structurally impossible to eventually
    conflate the two decode paths.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "purpose": _MFA_CHALLENGE_PURPOSE,
        "iat": now,
        "exp": now + timedelta(minutes=MFA_CHALLENGE_TOKEN_EXPIRY_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_mfa_challenge_token(token: str) -> int:
    """Decode and verify an MFA challenge token, returning the user_id it was
    issued for. Raises AuthenticationError if invalid, expired, or not
    actually an MFA challenge token (e.g. someone passing a real access
    token here instead)."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as error:
        raise AuthenticationError("MFA challenge has expired. Log in again.") from error
    except jwt.InvalidTokenError as error:
        raise AuthenticationError("Invalid MFA challenge.") from error

    if payload.get("purpose") != _MFA_CHALLENGE_PURPOSE:
        raise AuthenticationError("Invalid MFA challenge.")

    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError) as error:
        raise AuthenticationError("Invalid MFA challenge.") from error


def encrypt_secret(plaintext: str) -> str:
    """Symmetrically encrypt a secret (currently: a user's TOTP secret) for
    storage at rest, using MFA_ENCRYPTION_KEY. Unlike a password, this must
    be reversible to verify future codes, so it's encrypted, not hashed."""
    return _fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    """Reverse encrypt_secret(). Raises AuthenticationError if the ciphertext
    is invalid or was encrypted under a different MFA_ENCRYPTION_KEY (e.g.
    the key was rotated) -- treated as an auth failure, not a 500, since the
    caller's only real recourse at that point is a recovery code."""
    try:
        return _fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as error:
        raise AuthenticationError("Could not decrypt MFA secret.") from error
