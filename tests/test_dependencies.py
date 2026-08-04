"""Tests for src/api/dependencies.py's admin authorization dependencies."""

from datetime import datetime, timezone

import pytest

from src.api.dependencies import require_admin, require_super_admin
from src.core.exceptions import AuthorizationError
from src.financial.users.models import User
from src.financial.users.role import PlatformRole


def _build_user(role: PlatformRole) -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=1,
        username="alice",
        email="alice@example.com",
        password_hash="hashed-value",
        is_active=True,
        role=role,
        created_at=now,
        updated_at=now,
    )


def test_require_admin_allows_admin() -> None:
    user = _build_user(PlatformRole.ADMIN)

    assert require_admin(current_user=user) is user


def test_require_admin_allows_super_admin() -> None:
    user = _build_user(PlatformRole.SUPER_ADMIN)

    assert require_admin(current_user=user) is user


def test_require_admin_rejects_plain_user() -> None:
    user = _build_user(PlatformRole.USER)

    with pytest.raises(AuthorizationError):
        require_admin(current_user=user)


def test_require_super_admin_allows_super_admin() -> None:
    user = _build_user(PlatformRole.SUPER_ADMIN)

    assert require_super_admin(current_user=user) is user


def test_require_super_admin_rejects_admin() -> None:
    user = _build_user(PlatformRole.ADMIN)

    with pytest.raises(AuthorizationError):
        require_super_admin(current_user=user)


def test_require_super_admin_rejects_plain_user() -> None:
    user = _build_user(PlatformRole.USER)

    with pytest.raises(AuthorizationError):
        require_super_admin(current_user=user)
