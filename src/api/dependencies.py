"""Shared FastAPI dependencies."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.exceptions import AuthenticationError, NotFoundError
from src.core.security import decode_access_token
from src.financial.users import service as user_service
from src.financial.users.models import User

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
        return user_service.get_user(user_id)
    except NotFoundError as error:
        raise AuthenticationError("User account no longer exists.") from error
