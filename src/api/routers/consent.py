"""Consent API endpoints."""

from fastapi import APIRouter, Depends

from src.api.dependencies import require_recent_auth
from src.api.schemas.consent import ConsentActionRequest, ConsentRecordResponse
from src.financial.consent import service as consent_service
from src.financial.users.models import User

router = APIRouter(prefix="/consent", tags=["Consent"])


@router.post("/grant", response_model=ConsentRecordResponse)
def grant_consent(
    request: ConsentActionRequest, current_user: User = Depends(require_recent_auth)
) -> ConsentRecordResponse:
    """Grant consent for the current user, or for a linked child (guardian
    acting on the child's behalf). Step-up gated -- a legally-relevant
    record."""
    subject_user_id = request.subject_user_id or current_user.id
    record = consent_service.grant_consent(
        current_user, subject_user_id, request.consent_type, request.policy_version, request.evidence
    )
    return ConsentRecordResponse.model_validate(record)


@router.post("/revoke", response_model=ConsentRecordResponse)
def revoke_consent(
    request: ConsentActionRequest, current_user: User = Depends(require_recent_auth)
) -> ConsentRecordResponse:
    """Revoke consent for the current user, or for a linked child. Same
    authorization rules and step-up gating as grant."""
    subject_user_id = request.subject_user_id or current_user.id
    record = consent_service.revoke_consent(
        current_user, subject_user_id, request.consent_type, request.policy_version, request.evidence
    )
    return ConsentRecordResponse.model_validate(record)
