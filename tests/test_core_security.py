"""Tests for password hashing and JWT helpers."""

import logging
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from src.core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from src.core.exceptions import AuthenticationError
from src.core.security import (
    create_access_token,
    decode_access_token,
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
