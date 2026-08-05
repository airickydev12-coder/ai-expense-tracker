from datetime import datetime, timezone

import pytest

from src.financial.households.models import HouseholdMembership, HouseholdRole, RelationshipStatus
from src.financial.households.repository import (
    create_guardian_child_relationship,
    create_household,
    create_learning_profile,
    get_household_by_id,
    get_learning_profile,
    get_relationship,
    list_household_memberships_for_user,
    list_relationships_for_guardian,
    load_household_memberships_from_file,
    revoke_all_relationships_for_child,
    save_household_memberships_to_file,
)
from src.financial.households.models import AgeBand

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_create_and_get_household(db_path):
    household = create_household("Smith Family", db_path)

    assert household.id > 0
    assert household.name == "Smith Family"
    assert get_household_by_id(household.id, db_path) == household


def test_get_household_by_id_returns_none_when_missing(db_path):
    assert get_household_by_id(999, db_path) is None


def test_save_and_load_household_memberships(db_path):
    household = create_household("Smith Family", db_path)
    memberships = [
        HouseholdMembership(household.id, 1, HouseholdRole.OWNER, NOW),
        HouseholdMembership(household.id, 2, HouseholdRole.CHILD_LEARNER, NOW),
    ]

    save_household_memberships_to_file(memberships, household.id, db_path)

    assert load_household_memberships_from_file(household.id, db_path) == memberships


def test_load_household_memberships_returns_empty_list_when_none(db_path):
    assert load_household_memberships_from_file(999, db_path) == []


def test_list_household_memberships_for_user_spans_households(db_path):
    household_a = create_household("House A", db_path)
    household_b = create_household("House B", db_path)
    save_household_memberships_to_file(
        [HouseholdMembership(household_a.id, 1, HouseholdRole.OWNER, NOW)], household_a.id, db_path
    )
    save_household_memberships_to_file(
        [HouseholdMembership(household_b.id, 1, HouseholdRole.ADULT_MEMBER, NOW)], household_b.id, db_path
    )

    memberships = list_household_memberships_for_user(1, db_path)

    assert {m.household_id for m in memberships} == {household_a.id, household_b.id}


def test_create_and_get_guardian_child_relationship(db_path):
    relationship = create_guardian_child_relationship(1, 2, RelationshipStatus.ACTIVE, db_path)

    assert relationship.guardian_user_id == 1
    assert relationship.child_user_id == 2
    assert relationship.status == RelationshipStatus.ACTIVE
    assert get_relationship(1, 2, db_path) == relationship


def test_get_relationship_returns_none_when_missing(db_path):
    assert get_relationship(1, 2, db_path) is None


def test_list_relationships_for_guardian_filters_by_status(db_path):
    create_guardian_child_relationship(1, 2, RelationshipStatus.ACTIVE, db_path)
    create_guardian_child_relationship(1, 3, RelationshipStatus.REVOKED, db_path)

    active_only = list_relationships_for_guardian(1, RelationshipStatus.ACTIVE, db_path)
    everything = list_relationships_for_guardian(1, None, db_path)

    assert [r.child_user_id for r in active_only] == [2]
    assert {r.child_user_id for r in everything} == {2, 3}


def test_revoke_all_relationships_for_child_flips_every_row(db_path):
    create_guardian_child_relationship(1, 5, RelationshipStatus.ACTIVE, db_path)
    create_guardian_child_relationship(2, 5, RelationshipStatus.ACTIVE, db_path)

    revoke_all_relationships_for_child(5, db_path)

    relationship_1 = get_relationship(1, 5, db_path)
    relationship_2 = get_relationship(2, 5, db_path)
    assert relationship_1 is not None
    assert relationship_2 is not None
    assert relationship_1.status == RelationshipStatus.REVOKED
    assert relationship_2.status == RelationshipStatus.REVOKED


def test_revoke_all_relationships_for_child_is_idempotent(db_path):
    create_guardian_child_relationship(1, 5, RelationshipStatus.ACTIVE, db_path)

    revoke_all_relationships_for_child(5, db_path)
    revoke_all_relationships_for_child(5, db_path)  # must not raise

    relationship = get_relationship(1, 5, db_path)
    assert relationship is not None
    assert relationship.status == RelationshipStatus.REVOKED


def test_create_and_get_learning_profile(db_path):
    profile = create_learning_profile(1, AgeBand.AGE_6_9, True, db_path)

    assert profile.user_id == 1
    assert profile.age_band == AgeBand.AGE_6_9
    assert profile.ai_coach_enabled is True
    assert get_learning_profile(1, db_path) == profile


def test_get_learning_profile_returns_none_when_missing(db_path):
    assert get_learning_profile(999, db_path) is None
