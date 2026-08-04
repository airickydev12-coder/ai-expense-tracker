"""Admin API endpoints.

Platform-operator console. This module currently only proves the
authorization foundation works end-to-end -- real operational pages (user
management, security, notifications, system health, audit log) are staged
future work. Every route here must be gated behind require_admin (or
require_super_admin for the stricter tier) -- there is no other
authorization layer.
"""

from fastapi import APIRouter, Depends

from src.api.dependencies import require_admin, require_recent_admin, require_recent_super_admin
from src.api.schemas.admin import AssignRoleRequest, UpdateUserActiveRequest
from src.api.schemas.auth import UserResponse
from src.financial.users import admin_service
from src.financial.users.models import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/overview")
def overview(current_user: User = Depends(require_admin)) -> dict[str, str]:
    """Confirm admin access and identify the requesting admin.

    A stub for now -- real operational metrics (user counts, AI/notification
    health, etc.) are a later stage once this authorization foundation is
    in place.
    """
    return {
        "message": "Admin access confirmed.",
        "admin_username": current_user.username,
        "admin_role": current_user.role.value,
    }


@router.get("/users", response_model=list[UserResponse])
def list_users(current_user: User = Depends(require_admin)) -> list[User]:
    """List every user account, active and inactive."""
    return admin_service.list_users()


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current_user: User = Depends(require_admin)) -> User:
    """Return a single user account by id."""
    return admin_service.get_user_detail(user_id)


@router.patch("/users/{user_id}/active", response_model=UserResponse)
def set_user_active(
    user_id: int,
    request: UpdateUserActiveRequest,
    current_user: User = Depends(require_recent_admin),
) -> User:
    """Activate or deactivate a user account.

    Deactivating also revokes every refresh token the account holds --
    see admin_service.set_user_active_status for why.
    """
    return admin_service.set_user_active_status(current_user, user_id, request.is_active)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def assign_user_role(
    user_id: int,
    request: AssignRoleRequest,
    current_user: User = Depends(require_recent_super_admin),
) -> User:
    """Assign a user's platform role. Requires SUPER_ADMIN."""
    return admin_service.assign_role(current_user, user_id, request.role)


@router.post("/users/{user_id}/revoke-sessions", status_code=204)
def revoke_user_sessions(
    user_id: int,
    current_user: User = Depends(require_admin),
) -> None:
    """Revoke every refresh token belonging to a user, ending all their sessions."""
    admin_service.revoke_user_sessions(current_user, user_id)
