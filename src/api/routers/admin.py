"""Admin API endpoints.

Platform-operator console. This module currently only proves the
authorization foundation works end-to-end -- real operational pages (user
management, security, notifications, system health, audit log) are staged
future work. Every route here must be gated behind require_admin (or
require_super_admin for the stricter tier) -- there is no other
authorization layer.
"""

from fastapi import APIRouter, Depends

from src.api.dependencies import require_admin
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
