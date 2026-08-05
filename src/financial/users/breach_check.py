"""Breached-password screening via the HaveIBeenPwned k-anonymity API.

Soft warning only -- a password found in a known breach is never blocked
from being set. Registration, change-password, and reset-password must all
remain available even against a false positive or an unreachable API, so
any failure calling HIBP (network error, timeout, non-2xx response) is
swallowed and treated as "not known to be breached," never surfaced as an
error to the caller. This mirrors the project's existing soft-gate pattern
for email verification.

Only a truncated SHA-1 hash prefix of the password is ever sent to HIBP,
per its k-anonymity protocol -- the plaintext password never leaves the
server. SHA-1 here is mandated by that protocol, not used for the app's own
password storage (which remains Argon2id via src/core/security.py).
"""

import hashlib

import httpx

from src.core import config
from src.core.logging import get_logger

logger = get_logger(__name__)


def _request_breach_range(sha1_prefix: str) -> str:
    """Call the HIBP range API for a 5-char SHA-1 prefix.

    Returns the raw response body ("SUFFIX:COUNT" lines, one per known
    breached password sharing this prefix). Kept thin and separately
    monkeypatchable so tests never make a live network call.
    """
    response = httpx.get(
        f"{config.HIBP_API_URL}/{sha1_prefix}",
        timeout=config.HIBP_API_TIMEOUT_SECONDS,
        headers={"Add-Padding": "true"},
    )
    response.raise_for_status()
    return response.text


def is_password_breached(password: str) -> bool:
    """Return True if the password appears in the HIBP breach corpus.

    Fails open: any error reaching the API is logged and treated as
    "unknown," returning False -- this check must never block or delay a
    password-set action.
    """
    sha1_hash = hashlib.sha1(password.encode("utf-8"), usedforsecurity=False).hexdigest().upper()
    prefix, suffix = sha1_hash[:5], sha1_hash[5:]

    try:
        body = _request_breach_range(prefix)
    except httpx.HTTPError as exc:
        logger.warning("Breached-password check unavailable: %s", exc)
        return False

    for line in body.splitlines():
        line_suffix, _, _count = line.partition(":")
        if line_suffix.strip() == suffix:
            return True

    return False
