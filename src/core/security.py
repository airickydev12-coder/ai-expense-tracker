"""
Password hashing and JWT access-token helpers for the Financial Core application.

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

from src.core.config import JWT_ALGORITHM, JWT_EXPIRY_MINUTES, JWT_SECRET_KEY
from src.core.exceptions import AuthenticationError

_hasher = PasswordHasher()


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
    """Decode and verify a JWT access token, raising AuthenticationError if invalid."""
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as error:
        raise AuthenticationError("Token has expired.") from error
    except jwt.InvalidTokenError as error:
        raise AuthenticationError("Invalid authentication token.") from error
