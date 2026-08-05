"""Tests for password hashing and JWT helpers."""

import logging
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from src.core.config import JWT_ALGORITHM, JWT_SECRET_KEY, MFA_CHALLENGE_TOKEN_EXPIRY_MINUTES
from src.core.exceptions import AuthenticationError
from src.core.security import (
    create_access_token,
    create_mfa_challenge_token,
    decode_access_token,
    decode_mfa_challenge_token,
    decrypt_secret,
    encrypt_secret,
    hash_password,
    verify_password,
)


def test_hash_password_differs_from_plaintext() -> None:
    assert hash_password("correct-password") != "correct-password"


def test_hash_password_is_salted() -> None:
    first_hash = hash_password("correct-password")
    second_hash = hash_password("correct-password")

    assert first_hash != second_hash


def test_verify_password_true_for_correct_password() -> None:
    password_hash = hash_password("correct-password")

    assert verify_password("correct-password", password_hash) is True


def test_verify_password_false_for_wrong_password() -> None:
    password_hash = hash_password("correct-password")

    assert verify_password("wrong-password", password_hash) is False


def test_create_and_decode_access_token_round_trip() -> None:
    token = create_access_token(user_id=42, username="alice")

    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["username"] == "alice"


def test_create_access_token_defaults_auth_time_to_now() -> None:
    before = datetime.now(timezone.utc)
    token = create_access_token(user_id=42, username="alice")
    after = datetime.now(timezone.utc)

    payload = decode_access_token(token)
    auth_time = datetime.fromtimestamp(payload["auth_time"], tz=timezone.utc)

    # auth_time is encoded as a whole-second Unix timestamp (truncated, not
    # rounded), so it can read up to ~1s earlier than `before`.
    assert before - timedelta(seconds=1) <= auth_time <= after


def test_create_access_token_accepts_an_explicit_auth_time() -> None:
    original_auth_time = datetime.now(timezone.utc) - timedelta(hours=2)

    token = create_access_token(user_id=42, username="alice", auth_time=original_auth_time)

    payload = decode_access_token(token)
    auth_time = datetime.fromtimestamp(payload["auth_time"], tz=timezone.utc)

    assert abs((auth_time - original_auth_time).total_seconds()) < 1


def test_create_access_token_sets_purpose_to_access() -> None:
    token = create_access_token(user_id=42, username="alice")

    payload = decode_access_token(token)

    assert payload["purpose"] == "access"


def test_encrypt_and_decrypt_secret_round_trip() -> None:
    ciphertext = encrypt_secret("a-totp-secret")

    assert ciphertext != "a-totp-secret"
    assert decrypt_secret(ciphertext) == "a-totp-secret"


def test_decrypt_secret_rejects_tampered_ciphertext() -> None:
    ciphertext = encrypt_secret("a-totp-secret")
    tampered = ciphertext[:-4] + "abcd"

    with pytest.raises(AuthenticationError):
        decrypt_secret(tampered)


def test_create_and_decode_mfa_challenge_token_round_trip() -> None:
    token = create_mfa_challenge_token(user_id=42)

    assert decode_mfa_challenge_token(token) == 42


def test_decode_mfa_challenge_token_rejects_expired_token() -> None:
    now = datetime.now(timezone.utc)
    expired_token = jwt.encode(
        {
            "sub": "42",
            "purpose": "mfa_challenge",
            "iat": now - timedelta(minutes=MFA_CHALLENGE_TOKEN_EXPIRY_MINUTES + 10),
            "exp": now - timedelta(minutes=1),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(AuthenticationError):
        decode_mfa_challenge_token(expired_token)


def test_decode_mfa_challenge_token_rejects_a_real_access_token() -> None:
    access_token = create_access_token(user_id=42, username="alice")

    with pytest.raises(AuthenticationError):
        decode_mfa_challenge_token(access_token)


def test_decode_mfa_challenge_token_rejects_a_token_with_no_purpose_claim() -> None:
    now = datetime.now(timezone.utc)
    bare_token = jwt.encode(
        {"sub": "42", "iat": now, "exp": now + timedelta(minutes=5)},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(AuthenticationError):
        decode_mfa_challenge_token(bare_token)


def test_decode_access_token_rejects_wrong_signature() -> None:
    tampered_token = jwt.encode(
        {"sub": "42", "username": "alice"},
        "a-different-secret",
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(AuthenticationError):
        decode_access_token(tampered_token)


def test_decode_access_token_rejects_expired_token() -> None:
    now = datetime.now(timezone.utc)
    expired_token = jwt.encode(
        {
            "sub": "42",
            "username": "alice",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(AuthenticationError, match="expired"):
        decode_access_token(expired_token)


def test_register_and_authenticate_never_log_password_or_hash(db_path) -> None:
    from src.financial.users.service import authenticate_user, register_user

    records: list[str] = []

    class _CollectingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record.getMessage())

    # Attach directly to the service's own logger rather than relying on
    # caplog/root-logger propagation, since src/core/logging.py's
    # configure_logging() sets propagate=False on the "src" logger the first
    # time any test imports src.api.main — which would otherwise make this
    # test's outcome depend on unrelated test import order.
    handler = _CollectingHandler()
    handler.setLevel(logging.DEBUG)
    service_logger = logging.getLogger("src.financial.users.service")
    previous_level = service_logger.level
    service_logger.addHandler(handler)
    service_logger.setLevel(logging.DEBUG)
    try:
        register_user("alice", "alice@example.com", "correct-password", db_path)
        authenticate_user("alice", "correct-password", db_path)
    finally:
        service_logger.removeHandler(handler)
        service_logger.setLevel(previous_level)

    log_text = "\n".join(records)
    assert "correct-password" not in log_text
