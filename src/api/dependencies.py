"""Shared FastAPI dependencies."""

from datetime import datetime, timedelta, timezone

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.config import STEP_UP_MAX_AGE_MINUTES
from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    StepUpRequiredError,
)
from src.core.security import decode_access_token
from src.financial.users import service as user_service
from src.financial.users.models import User
from src.financial.users.role import PlatformRole

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> User:
    """Resolve the authenticated user from a bearer JWT, or raise AuthenticationError."""
    if credentials is None:
        raise AuthenticationError("Missing bearer token.")

    payload = decode_access_token(credentials.credentials)

    # A missing "purpose" defaults to "access" for backward compatibility
    # with tokens minted before this claim existed -- a real MFA challenge
    # token (see create_mfa_challenge_token()) always explicitly carries
    # purpose="mfa_challenge", so this only ever excludes non-access tokens,
    # never silently rejects an old-but-otherwise-valid access token. Without
    # this check, an intercepted MFA challenge token -- itself a validly
    # signed JWT with a "sub" claim -- could be replayed here as a bearer
    # token and authenticate as that user before they ever complete MFA.
    if payload.get("purpose", "access") != "access":
        raise AuthenticationError("Invalid authentication token.")

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as error:
        raise AuthenticationError("Malformed authentication token.") from error

    try:
        user = user_service.get_user(user_id)
    except NotFoundError as error:
        raise AuthenticationError("User account no longer exists.") from error

    if not user.is_active:
        raise AuthenticationError("This account has been deactivated.")

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Resolve the current user, requiring platform ADMIN or SUPER_ADMIN.

    A super-admin can do everything an admin can, so both satisfy this --
    require_super_admin below is the stricter tier for actions (like
    assigning platform roles) an admin alone shouldn't be able to perform.
    """
    if current_user.role not in (PlatformRole.ADMIN, PlatformRole.SUPER_ADMIN):
        raise AuthorizationError("Administrator access is required.")

    return current_user


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Resolve the current user, requiring platform SUPER_ADMIN specifically."""
    if current_user.role != PlatformRole.SUPER_ADMIN:
        raise AuthorizationError("Super-administrator access is required.")

    return current_user


def _assert_recent_auth(credentials: HTTPAuthorizationCredentials | None) -> None:
    """Raise StepUpRequiredError unless the caller's access token's auth_time
    (last real password verification -- see create_access_token()) is within
    STEP_UP_MAX_AGE_MINUTES.

    Re-decodes the token rather than threading the payload through from
    get_current_user() -- a second cheap JWT decode of an already-validated
    token, same tradeoff get_current_user() itself makes to read `sub`.
    """
    if credentials is None:
        raise AuthenticationError("Missing bearer token.")

    payload = decode_access_token(credentials.credentials)
    auth_time = payload.get("auth_time")

    if auth_time is None:
        raise StepUpRequiredError("Recent authentication required for this action.")

    auth_time_dt = datetime.fromtimestamp(auth_time, tz=timezone.utc)
    max_age = timedelta(minutes=STEP_UP_MAX_AGE_MINUTES)

    if datetime.now(timezone.utc) - auth_time_dt > max_age:
        raise StepUpRequiredError("Recent authentication required for this action.")


def require_recent_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    current_user: User = Depends(get_current_user),
) -> User:
    """Resolve the current user, additionally requiring a recent (step-up)
    auth_time -- for self-service actions with no authorization tier of
    their own beyond being logged in (e.g. revoking all sessions)."""
    _assert_recent_auth(credentials)
    return current_user


def require_recent_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    current_user: User = Depends(require_admin),
) -> User:
    """require_admin, additionally requiring a recent (step-up) auth_time."""
    _assert_recent_auth(credentials)
    return current_user


def require_recent_super_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    current_user: User = Depends(require_super_admin),
) -> User:
    """require_super_admin, additionally requiring a recent (step-up) auth_time."""
    _assert_recent_auth(credentials)
    return current_user
