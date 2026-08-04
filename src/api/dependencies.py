"""Shared FastAPI dependencies."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.exceptions import AuthenticationError, AuthorizationError, NotFoundError
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
