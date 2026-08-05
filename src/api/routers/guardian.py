"""Guardian API endpoints."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user
from src.api.schemas.auth import UserResponse
from src.api.schemas.households import ChildSummaryResponse, GuardianChildRelationshipResponse
from src.financial.households import service as household_service
from src.financial.users.models import User

router = APIRouter(prefix="/guardian", tags=["Guardian"])


@router.get("/children", response_model=list[ChildSummaryResponse])
def list_children(current_user: User = Depends(get_current_user)) -> list[ChildSummaryResponse]:
    """Return the current user's linked children (active relationships only)."""
    children = household_service.list_children_for_guardian(current_user)
    return [
        ChildSummaryResponse(
            child=UserResponse.model_validate(child),
            relationship=GuardianChildRelationshipResponse.model_validate(relationship),
        )
        for child, relationship in children
    ]
