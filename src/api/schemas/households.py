"""API schemas for household/guardian-child endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.api.schemas.auth import UserResponse
from src.api.schemas.consent import ConsentRecordResponse
from src.financial.households.models import AgeBand, HouseholdRole, RelationshipStatus


class HouseholdCreateRequest(BaseModel):
    """Request body for creating a household."""

    name: str = Field(min_length=1, max_length=100)


class HouseholdMembershipResponse(BaseModel):
    """Serialized representation of one household membership row."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    household_role: HouseholdRole
    joined_at: datetime


class HouseholdResponse(BaseModel):
    """Serialized representation of a household, including its members."""

    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    members: list[HouseholdMembershipResponse]


class AddMemberRequest(BaseModel):
    """Request body for adding a member to a household."""

    user_id: int
    household_role: HouseholdRole


class GuardianChildRelationshipResponse(BaseModel):
    """Serialized representation of a guardian-child relationship."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    guardian_user_id: int
    child_user_id: int
    status: RelationshipStatus
    created_at: datetime
    revoked_at: datetime | None


class LearningProfileResponse(BaseModel):
    """Serialized representation of a MINOR account's learning profile."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    age_band: AgeBand
    ai_coach_enabled: bool
    created_at: datetime
    updated_at: datetime


class ChildAccountCreateRequest(BaseModel):
    """Request body for a guardian-initiated child account creation.

    Same (username, email, password) shape as ordinary registration -- the
    guardian supplies all three on the child's behalf. policy_version and
    evidence back the initial ACCOUNT_CREATION consent record (see
    ConsentRecord).
    """

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    age_band: AgeBand
    policy_version: str = Field(min_length=1)
    evidence: str = Field(min_length=1)


class ChildAccountCreateResponse(BaseModel):
    """Everything created by one guardian-initiated child account creation."""

    child: UserResponse
    relationship: GuardianChildRelationshipResponse
    learning_profile: LearningProfileResponse
    consent_record: ConsentRecordResponse


class ChildSummaryResponse(BaseModel):
    """One entry in a guardian's linked-children list."""

    child: UserResponse
    relationship: GuardianChildRelationshipResponse
