from datetime import datetime, timezone

import pytest

from src.financial.households.models import (
    AgeBand,
    GuardianChildRelationship,
    Household,
    HouseholdMembership,
    HouseholdRole,
    LearningProfile,
    RelationshipStatus,
)

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_household_rejects_empty_name():
    with pytest.raises(ValueError, match="name cannot be empty"):
        Household(id=1, name="   ", created_at=NOW, updated_at=NOW)


def test_household_rejects_non_positive_id():
    with pytest.raises(ValueError, match="greater than zero"):
        Household(id=0, name="Smith Family", created_at=NOW, updated_at=NOW)


def test_household_to_dict_and_from_dict_round_trip():
    household = Household(id=1, name="Smith Family", created_at=NOW, updated_at=NOW)
    assert Household.from_dict(household.to_dict()) == household


def test_household_membership_coerces_str_role():
    membership = HouseholdMembership(
        household_id=1, user_id=2, household_role="owner", joined_at=NOW  # type: ignore[arg-type]
    )
    assert membership.household_role == HouseholdRole.OWNER


def test_household_membership_to_dict_and_from_dict_round_trip():
    membership = HouseholdMembership(
        household_id=1, user_id=2, household_role=HouseholdRole.GUARDIAN, joined_at=NOW
    )
    assert HouseholdMembership.from_dict(membership.to_dict()) == membership


def test_guardian_child_relationship_round_trip_with_revoked_at():
    relationship = GuardianChildRelationship(
        id=1,
        guardian_user_id=2,
        child_user_id=3,
        status=RelationshipStatus.REVOKED,
        created_at=NOW,
        revoked_at=NOW,
    )
    assert GuardianChildRelationship.from_dict(relationship.to_dict()) == relationship


def test_guardian_child_relationship_defaults_revoked_at_to_none():
    relationship = GuardianChildRelationship(
        id=1, guardian_user_id=2, child_user_id=3, status=RelationshipStatus.ACTIVE, created_at=NOW
    )
    assert relationship.revoked_at is None


def test_learning_profile_age_band_hyphenated_value_coercion():
    profile = LearningProfile(
        user_id=1,
        age_band="6-9",  # type: ignore[arg-type]
        ai_coach_enabled=True,
        created_at=NOW,
        updated_at=NOW,
    )
    assert profile.age_band == AgeBand.AGE_6_9
    assert profile.age_band.value == "6-9"


def test_learning_profile_to_dict_and_from_dict_round_trip():
    profile = LearningProfile(
        user_id=1, age_band=AgeBand.AGE_10_13, ai_coach_enabled=False, created_at=NOW, updated_at=NOW
    )
    assert LearningProfile.from_dict(profile.to_dict()) == profile
