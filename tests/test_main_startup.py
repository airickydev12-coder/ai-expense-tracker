"""Tests for src/api/main.py's startup config validation."""

import pytest

from src.api import main


def test_validate_startup_config_raises_in_production_with_insecure_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "ENVIRONMENT", "production")
    monkeypatch.setattr(main, "JWT_SECRET_KEY", main._INSECURE_JWT_SECRET)

    with pytest.raises(RuntimeError):
        main._validate_startup_config()


def test_validate_startup_config_allows_production_with_a_real_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "ENVIRONMENT", "production")
    monkeypatch.setattr(main, "JWT_SECRET_KEY", "a-real-random-secret")
    monkeypatch.setattr(main, "MFA_ENCRYPTION_KEY", "a-real-random-fernet-key")
    monkeypatch.setattr(main, "COOKIE_SECURE", True)

    main._validate_startup_config()


def test_validate_startup_config_only_warns_in_development_with_insecure_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "ENVIRONMENT", "development")
    monkeypatch.setattr(main, "JWT_SECRET_KEY", main._INSECURE_JWT_SECRET)

    main._validate_startup_config()


def test_validate_startup_config_never_raises_for_cookie_secure_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "ENVIRONMENT", "production")
    monkeypatch.setattr(main, "JWT_SECRET_KEY", "a-real-random-secret")
    monkeypatch.setattr(main, "MFA_ENCRYPTION_KEY", "a-real-random-fernet-key")
    monkeypatch.setattr(main, "COOKIE_SECURE", False)

    main._validate_startup_config()


def test_validate_startup_config_raises_in_production_with_insecure_mfa_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "ENVIRONMENT", "production")
    monkeypatch.setattr(main, "JWT_SECRET_KEY", "a-real-random-secret")
    monkeypatch.setattr(main, "MFA_ENCRYPTION_KEY", main._INSECURE_MFA_ENCRYPTION_KEY)

    with pytest.raises(RuntimeError):
        main._validate_startup_config()


def test_validate_startup_config_only_warns_in_development_with_insecure_mfa_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "ENVIRONMENT", "development")
    monkeypatch.setattr(main, "MFA_ENCRYPTION_KEY", main._INSECURE_MFA_ENCRYPTION_KEY)

    main._validate_startup_config()
