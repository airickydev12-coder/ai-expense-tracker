import pytest

from src.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from src.financial.households import service as household_service
from src.financial.households.models import AgeBand, HouseholdRole, RelationshipStatus
from src.financial.households.repository import get_relationship
from src.financial.users import service as user_service
from src.financial.users.account_type import AccountType


def _make_user(db_path, username="alice", account_type=AccountType.ADULT):
    return user_service.create_user_account(
        username, f"{username}@example.com", "correct-password", account_type=account_type, db_path=db_path
    )


def test_create_household_adds_actor_as_owner(db_path):
    actor = _make_user(db_path)

    household = household_service.create_household(actor, "Smith Family", db_path)

    members = household_service.list_members(household.id, db_path)
    assert len(members) == 1
    assert members[0].user_id == actor.id
    assert members[0].household_role == HouseholdRole.OWNER


def test_create_household_rejects_minor_actor(db_path):
    minor = _make_user(db_path, "kid", account_type=AccountType.MINOR)

    with pytest.raises(AuthorizationError):
        household_service.create_household(minor, "Kid's Household", db_path)


def test_get_household_for_member_raises_not_found_for_non_member(db_path):
    owner = _make_user(db_path, "owner")
    outsider = _make_user(db_path, "outsider")
    household = household_service.create_household(owner, "Smith Family", db_path)

    with pytest.raises(NotFoundError):
        household_service.get_household_for_member(outsider, household.id, db_path)


def test_get_household_for_member_raises_not_found_for_unknown_household(db_path):
    owner = _make_user(db_path, "owner")

    with pytest.raises(NotFoundError):
        household_service.get_household_for_member(owner, 999, db_path)


def test_add_member_rejects_duplicate_membership(db_path):
    owner = _make_user(db_path, "owner")
    adult = _make_user(db_path, "adult")
    household = household_service.create_household(owner, "Smith Family", db_path)

    household_service.add_member(owner, household.id, adult.id, HouseholdRole.ADULT_MEMBER, db_path)

    with pytest.raises(ValidationError):
        household_service.add_member(owner, household.id, adult.id, HouseholdRole.ADULT_MEMBER, db_path)


def test_add_member_rejects_non_manager_actor(db_path):
    owner = _make_user(db_path, "owner")
    member = _make_user(db_path, "member")
    outsider = _make_user(db_path, "outsider")
    household = household_service.create_household(owner, "Smith Family", db_path)
    household_service.add_member(owner, household.id, member.id, HouseholdRole.ADULT_MEMBER, db_path)

    with pytest.raises(AuthorizationError):
        household_service.add_member(member, household.id, outsider.id, HouseholdRole.ADULT_MEMBER, db_path)


def test_add_member_rejects_minor_actor(db_path):
    minor = _make_user(db_path, "kid", account_type=AccountType.MINOR)
    other = _make_user(db_path, "other")
    owner = _make_user(db_path, "owner")
    household = household_service.create_household(owner, "Smith Family", db_path)

    with pytest.raises(AuthorizationError):
        household_service.add_member(minor, household.id, other.id, HouseholdRole.ADULT_MEMBER, db_path)


def test_remove_member_allows_self_removal_by_adult_member(db_path):
    owner = _make_user(db_path, "owner")
    member = _make_user(db_path, "member")
    household = household_service.create_household(owner, "Smith Family", db_path)
    household_service.add_member(owner, household.id, member.id, HouseholdRole.ADULT_MEMBER, db_path)

    household_service.remove_member(member, household.id, member.id, db_path)

    assert household_service.get_membership(household.id, member.id, db_path) is None


def test_remove_member_blocks_removing_the_owner(db_path):
    owner = _make_user(db_path, "owner")
    household = household_service.create_household(owner, "Smith Family", db_path)

    with pytest.raises(ValidationError):
        household_service.remove_member(owner, household.id, owner.id, db_path)


def test_remove_member_blocks_non_manager_removing_someone_else(db_path):
    owner = _make_user(db_path, "owner")
    member_a = _make_user(db_path, "member_a")
    member_b = _make_user(db_path, "member_b")
    household = household_service.create_household(owner, "Smith Family", db_path)
    household_service.add_member(owner, household.id, member_a.id, HouseholdRole.ADULT_MEMBER, db_path)
    household_service.add_member(owner, household.id, member_b.id, HouseholdRole.ADULT_MEMBER, db_path)

    with pytest.raises(AuthorizationError):
        household_service.remove_member(member_a, household.id, member_b.id, db_path)


def test_list_households_for_user_spans_multiple_households(db_path):
    actor = _make_user(db_path)
    household_a = household_service.create_household(actor, "House A", db_path)
    household_b = household_service.create_household(actor, "House B", db_path)

    households = household_service.list_households_for_user(actor.id, db_path)

    assert {h.id for h in households} == {household_a.id, household_b.id}


def test_create_child_account_creates_every_side_effect_row(db_path):
    guardian = _make_user(db_path, "guardian")
    household = household_service.create_household(guardian, "Smith Family", db_path)

    result = household_service.create_child_account(
        guardian, household.id, "kiddo", "kiddo@example.com", "correct-password",
        AgeBand.AGE_6_9, "v1", "guardian confirmed via API request", db_path,
    )

    assert result.child.account_type == AccountType.MINOR
    membership = household_service.get_membership(household.id, result.child.id, db_path)
    assert membership is not None
    assert membership.household_role == HouseholdRole.CHILD_LEARNER
    assert result.relationship.guardian_user_id == guardian.id
    assert result.relationship.child_user_id == result.child.id
    assert result.relationship.status == RelationshipStatus.ACTIVE
    assert result.learning_profile.age_band == AgeBand.AGE_6_9
    assert result.consent_record.subject_user_id == result.child.id
    assert result.consent_record.consented_by_user_id == guardian.id


def test_create_child_account_rejects_non_manager_actor(db_path):
    owner = _make_user(db_path, "owner")
    member = _make_user(db_path, "member")
    household = household_service.create_household(owner, "Smith Family", db_path)
    household_service.add_member(owner, household.id, member.id, HouseholdRole.ADULT_MEMBER, db_path)

    with pytest.raises(AuthorizationError):
        household_service.create_child_account(
            member, household.id, "kiddo", "kiddo@example.com", "correct-password",
            AgeBand.AGE_6_9, "v1", "evidence", db_path,
        )


def test_create_child_account_rejects_minor_actor(db_path):
    guardian = _make_user(db_path, "guardian")
    household = household_service.create_household(guardian, "Smith Family", db_path)
    minor = _make_user(db_path, "kid", account_type=AccountType.MINOR)
    household_service.add_member(guardian, household.id, minor.id, HouseholdRole.CHILD_LEARNER, db_path)

    with pytest.raises(AuthorizationError):
        household_service.create_child_account(
            minor, household.id, "kiddo2", "kiddo2@example.com", "correct-password",
            AgeBand.AGE_6_9, "v1", "evidence", db_path,
        )


def test_list_children_for_guardian_excludes_revoked(db_path):
    guardian = _make_user(db_path, "guardian")
    household = household_service.create_household(guardian, "Smith Family", db_path)
    result = household_service.create_child_account(
        guardian, household.id, "kiddo", "kiddo@example.com", "correct-password",
        AgeBand.AGE_10_13, "v1", "evidence", db_path,
    )

    children_before = household_service.list_children_for_guardian(guardian, db_path)
    assert len(children_before) == 1

    from src.financial.households.repository import revoke_all_relationships_for_child
    revoke_all_relationships_for_child(result.child.id, db_path)

    children_after = household_service.list_children_for_guardian(guardian, db_path)
    assert children_after == []


def test_request_adult_transition_flips_account_type_and_revokes_relationships(db_path):
    guardian_a = _make_user(db_path, "guardian_a")
    guardian_b = _make_user(db_path, "guardian_b")
    household = household_service.create_household(guardian_a, "Smith Family", db_path)
    result = household_service.create_child_account(
        guardian_a, household.id, "teen", "teen@example.com", "correct-password",
        AgeBand.AGE_14_17, "v1", "evidence", db_path,
    )
    from src.financial.households.repository import create_guardian_child_relationship
    create_guardian_child_relationship(guardian_b.id, result.child.id, RelationshipStatus.ACTIVE, db_path)

    transitioned = household_service.request_adult_transition(result.child, db_path)

    relationship_a = get_relationship(guardian_a.id, result.child.id, db_path)
    relationship_b = get_relationship(guardian_b.id, result.child.id, db_path)
    assert relationship_a is not None
    assert relationship_b is not None
    assert transitioned.account_type == AccountType.ADULT
    assert relationship_a.status == RelationshipStatus.REVOKED
    assert relationship_b.status == RelationshipStatus.REVOKED


def test_request_adult_transition_leaves_consent_records_untouched(db_path):
    guardian = _make_user(db_path, "guardian")
    household = household_service.create_household(guardian, "Smith Family", db_path)
    result = household_service.create_child_account(
        guardian, household.id, "teen", "teen@example.com", "correct-password",
        AgeBand.AGE_14_17, "v1", "evidence", db_path,
    )

    household_service.request_adult_transition(result.child, db_path)

    from src.financial.consent.repository import list_consent_records_for_subject
    records = list_consent_records_for_subject(result.child.id, db_path)
    assert len(records) == 1
    assert records[0].consented_by_user_id == guardian.id


def test_request_adult_transition_rejects_already_adult_actor(db_path):
    adult = _make_user(db_path)

    with pytest.raises(ValidationError):
        household_service.request_adult_transition(adult, db_path)
