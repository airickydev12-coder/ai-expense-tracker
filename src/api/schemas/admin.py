"""API schemas for admin endpoints."""

from pydantic import BaseModel

from src.financial.users.role import PlatformRole


class UpdateUserActiveRequest(BaseModel):
    """Request body for activating/deactivating a user account."""

    is_active: bool


class AssignRoleRequest(BaseModel):
    """Request body for assigning a user's platform role."""

    role: PlatformRole
