"""Adult-transition API endpoint -- kept separate from the plural
src/api/routers/accounts.py (financial accounts domain), an unrelated
concept that happens to share a name."""

from fastapi import APIRouter, Depends

from src.api.dependencies import require_recent_auth
from src.api.schemas.auth import UserResponse
from src.financial.households import service as household_service
from src.financial.users.models import User

router = APIRouter(prefix="/account", tags=["Account"])


@router.post("/request-adult-transition", response_model=UserResponse)
def request_adult_transition(current_user: User = Depends(require_recent_auth)) -> UserResponse:
    """Self-initiated: transition the current MINOR account to ADULT,
    revoking every guardian relationship for it in the same action.
    Step-up gated."""
    updated = household_service.request_adult_transition(current_user)
    return UserResponse.model_validate(updated)
