"""Household API endpoints."""

from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_current_user, require_recent_auth
from src.api.schemas.auth import UserResponse
from src.api.schemas.consent import ConsentRecordResponse
from src.api.schemas.households import (
    AddMemberRequest,
    ChildAccountCreateRequest,
    ChildAccountCreateResponse,
    GuardianChildRelationshipResponse,
    HouseholdCreateRequest,
    HouseholdMembershipResponse,
    HouseholdResponse,
    LearningProfileResponse,
)
from src.financial.households import service as household_service
from src.financial.users.models import User

router = APIRouter(prefix="/households", tags=["Households"])


def _to_household_response(household_id: int) -> HouseholdResponse:
    household = household_service.get_household(household_id)
    members = household_service.list_members(household_id)
    return HouseholdResponse(
        id=household.id,
        name=household.name,
        created_at=household.created_at,
        updated_at=household.updated_at,
        members=[HouseholdMembershipResponse.model_validate(m) for m in members],
    )


@router.post("", response_model=HouseholdResponse, status_code=status.HTTP_201_CREATED)
def create_household(
    request: HouseholdCreateRequest, current_user: User = Depends(get_current_user)
) -> HouseholdResponse:
    """Create a household, with the current user as its owner."""
    household = household_service.create_household(current_user, request.name)
    return _to_household_response(household.id)


@router.get("", response_model=list[HouseholdResponse])
def list_my_households(current_user: User = Depends(get_current_user)) -> list[HouseholdResponse]:
    """Return every household the current user belongs to (household selection)."""
    households = household_service.list_households_for_user(current_user.id)
    return [_to_household_response(household.id) for household in households]


@router.get("/{household_id}", response_model=HouseholdResponse)
def get_household(
    household_id: int, current_user: User = Depends(get_current_user)
) -> HouseholdResponse:
    """Return a household, if the current user is a member."""
    household_service.get_household_for_member(current_user, household_id)
    return _to_household_response(household_id)


@router.post("/{household_id}/members", response_model=HouseholdMembershipResponse)
def add_member(
    household_id: int,
    request: AddMemberRequest,
    current_user: User = Depends(get_current_user),
) -> HouseholdMembershipResponse:
    """Add a member to a household. Requires the current user to be the
    household's owner or a guardian."""
    membership = household_service.add_member(
        current_user, household_id, request.user_id, request.household_role
    )
    return HouseholdMembershipResponse.model_validate(membership)


@router.delete("/{household_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    household_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a member from a household. A member can always remove
    themselves; removing someone else requires being the household's owner
    or a guardian."""
    household_service.remove_member(current_user, household_id, user_id)


@router.post(
    "/{household_id}/children",
    response_model=ChildAccountCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_child_account(
    household_id: int,
    request: ChildAccountCreateRequest,
    current_user: User = Depends(require_recent_auth),
) -> ChildAccountCreateResponse:
    """Guardian-initiated: create a MINOR child account linked to this
    household, with an initial consent record. Step-up gated (creates a
    durable account with consent implications)."""
    result = household_service.create_child_account(
        current_user,
        household_id,
        request.username,
        request.email,
        request.password,
        request.age_band,
        request.policy_version,
        request.evidence,
    )
    return ChildAccountCreateResponse(
        child=UserResponse.model_validate(result.child),
        relationship=GuardianChildRelationshipResponse.model_validate(result.relationship),
        learning_profile=LearningProfileResponse.model_validate(result.learning_profile),
        consent_record=ConsentRecordResponse.model_validate(result.consent_record),
    )
