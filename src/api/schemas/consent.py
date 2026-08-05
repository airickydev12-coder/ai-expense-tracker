"""API schemas for consent endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.financial.consent.models import ConsentStatus, ConsentType


class ConsentActionRequest(BaseModel):
    """Request body for granting or revoking consent.

    subject_user_id defaults to None, meaning "self" -- resolved to the
    current user's own id by the router before calling the service.
    """

    subject_user_id: int | None = None
    consent_type: ConsentType
    policy_version: str = Field(min_length=1)
    evidence: str = Field(min_length=1)


class ConsentRecordResponse(BaseModel):
    """Serialized representation of one consent record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_user_id: int
    consented_by_user_id: int | None
    consent_type: ConsentType
    policy_version: str
    status: ConsentStatus
    granted_at: datetime | None
    revoked_at: datetime | None
    evidence: str
    created_at: datetime
