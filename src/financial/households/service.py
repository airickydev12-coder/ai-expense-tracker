from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.core.config import DB_PATH
from src.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from src.core.logging import get_logger
from src.financial.consent.models import ConsentRecord, ConsentType
from src.financial.consent.service import grant_consent
from src.financial.households.models import (
    AgeBand,
    GuardianChildRelationship,
    Household,
    HouseholdMembership,
    HouseholdRole,
    LearningProfile,
    RelationshipStatus,
)
from src.financial.households.repository import (
    create_guardian_child_relationship,
    create_household as create_household_row,
    create_learning_profile,
    get_household_by_id,
    list_household_memberships_for_user,
    list_relationships_for_guardian,
    load_household_memberships_from_file,
    revoke_all_relationships_for_child,
    save_household_memberships_to_file,
)
from src.financial.users.account_type import AccountType
from src.financial.users.models import User
from src.financial.users.repository import update_account_type
from src.financial.users.service import create_user_account, get_user

logger = get_logger(__name__)

household_memberships: dict[int, list[HouseholdMembership]] = {}


def _ensure_loaded(household_id: int, db_path: Path = DB_PATH) -> None:
    """Lazily load a household's memberships into the cache on first access."""
    if household_id not in household_memberships:
        household_memberships[household_id] = load_household_memberships_from_file(
            household_id, db_path
        )


def save_members(household_id: int, db_path: Path = DB_PATH) -> None:
    """Save a household's memberships using the repository."""
    save_household_memberships_to_file(household_memberships[household_id], household_id, db_path)


def get_household(household_id: int, db_path: Path = DB_PATH) -> Household:
    """Return a household by ID, or raise NotFoundError."""
    household = get_household_by_id(household_id, db_path)

    if household is None:
        raise NotFoundError(f"No household found with ID {household_id}.")

    return household


def get_membership(
    household_id: int, user_id: int, db_path: Path = DB_PATH
) -> HouseholdMembership | None:
    """Return a user's membership row in a household, or None."""
    _ensure_loaded(household_id, db_path)

    for membership in household_memberships[household_id]:
        if membership.user_id == user_id:
            return membership

    return None


def get_household_for_member(actor: User, household_id: int, db_path: Path = DB_PATH) -> Household:
    """Return a household, raising NotFoundError if it doesn't exist OR the
    actor isn't a member -- doesn't confirm a household's existence to
    non-members, matching account_service's existing not-my-resource
    convention."""
    household = get_household(household_id, db_path)

    if get_membership(household_id, actor.id, db_path) is None:
        raise NotFoundError(f"No household found with ID {household_id}.")

    return household


def list_members(household_id: int, db_path: Path = DB_PATH) -> list[HouseholdMembership]:
    """Return every membership row for a household."""
    _ensure_loaded(household_id, db_path)
    return household_memberships[household_id].copy()


def list_households_for_user(user_id: int, db_path: Path = DB_PATH) -> list[Household]:
    """Return every household a user belongs to -- the "household
    selection" list. Not cached: called once per "my households" request."""
    memberships = list_household_memberships_for_user(user_id, db_path)
    return [get_household(membership.household_id, db_path) for membership in memberships]


def _require_manager_membership(
    household_id: int, actor: User, db_path: Path = DB_PATH
) -> HouseholdMembership:
    """Shared guard for add_member/remove_member(others)/create_child_account:
    actor must hold OWNER or GUARDIAN in this household. Non-member ->
    NotFoundError (same "don't confirm existence" convention). Member but
    wrong role -> AuthorizationError."""
    membership = get_membership(household_id, actor.id, db_path)

    if membership is None:
        raise NotFoundError(f"No household found with ID {household_id}.")

    if membership.household_role not in (HouseholdRole.OWNER, HouseholdRole.GUARDIAN):
        raise AuthorizationError(
            "Only the household owner or a guardian can manage this household's members."
        )

    return membership


def create_household(actor: User, name: str, db_path: Path = DB_PATH) -> Household:
    """Create a household, adding the actor as its OWNER in the same call --
    a household is never created ownerless."""
    if actor.account_type == AccountType.MINOR:
        raise AuthorizationError("Minor accounts cannot manage households.")

    household = create_household_row(name, db_path)
    now = datetime.now(timezone.utc)
    household_memberships[household.id] = [
        HouseholdMembership(household.id, actor.id, HouseholdRole.OWNER, now)
    ]
    save_members(household.id, db_path)

    logger.info("User %d created household %d (%s)", actor.id, household.id, name)

    return household


def add_member(
    actor: User,
    household_id: int,
    target_user_id: int,
    household_role: HouseholdRole,
    db_path: Path = DB_PATH,
) -> HouseholdMembership:
    """Add a member to a household. Requires the actor to be an OWNER or
    GUARDIAN of the household; rejects a MINOR actor and a duplicate
    membership."""
    if actor.account_type == AccountType.MINOR:
        raise AuthorizationError("Minor accounts cannot manage households.")

    get_household(household_id, db_path)
    _require_manager_membership(household_id, actor, db_path)

    if get_membership(household_id, target_user_id, db_path) is not None:
        raise ValidationError("User is already a member of this household.")

    membership = HouseholdMembership(
        household_id, target_user_id, household_role, datetime.now(timezone.utc)
    )
    household_memberships[household_id].append(membership)
    save_members(household_id, db_path)

    logger.info(
        "User %d added user %d to household %d as %s",
        actor.id,
        target_user_id,
        household_id,
        household_role.value,
    )

    return membership


def remove_member(actor: User, household_id: int, target_user_id: int, db_path: Path = DB_PATH) -> None:
    """Remove a member from a household.

    Self-removal ("leave") is allowed for any non-owner role without
    needing manager status -- this is what makes "an adult member can leave
    a household" actually usable. Removing someone *else* requires manager
    (OWNER/GUARDIAN) membership. Removing the OWNER is always blocked --
    no ownership-transfer flow exists yet (known gap, not solved this
    sprint).
    """
    get_household(household_id, db_path)

    actor_membership = get_membership(household_id, actor.id, db_path)
    if actor_membership is None:
        raise NotFoundError(f"No household found with ID {household_id}.")

    target_membership = get_membership(household_id, target_user_id, db_path)
    if target_membership is None:
        raise NotFoundError(f"No membership found for user {target_user_id} in this household.")

    is_self_removal = target_user_id == actor.id
    if not is_self_removal and actor_membership.household_role not in (
        HouseholdRole.OWNER,
        HouseholdRole.GUARDIAN,
    ):
        raise AuthorizationError("Only the household owner or a guardian can remove other members.")

    if target_membership.household_role == HouseholdRole.OWNER:
        raise ValidationError("Cannot remove the household owner. Ownership transfer is not supported yet.")

    household_memberships[household_id] = [
        membership
        for membership in household_memberships[household_id]
        if membership.user_id != target_user_id
    ]
    save_members(household_id, db_path)

    logger.info("User %d removed user %d from household %d", actor.id, target_user_id, household_id)


@dataclass
class ChildAccountCreationResult:
    """Bundles every row created by a single guardian-initiated child
    account creation."""

    child: User
    relationship: GuardianChildRelationship
    learning_profile: LearningProfile
    consent_record: ConsentRecord


def create_child_account(
    actor: User,
    household_id: int,
    username: str,
    email: str,
    password: str,
    age_band: AgeBand,
    policy_version: str,
    evidence: str,
    db_path: Path = DB_PATH,
) -> ChildAccountCreationResult:
    """Guardian-initiated: creates a MINOR user account, a CHILD_LEARNER
    household membership, an ACTIVE guardian-child relationship, a learning
    profile, and an initial ACCOUNT_CREATION consent record, in one call.

    Known, accepted gap: these are 5 separate repository writes across 3
    tables, not one SQLite transaction -- this codebase never wraps
    multi-table writes in a single cross-repository-call transaction
    anywhere (e.g. register_user() creates the user then separately sends
    an email, not atomic either). A failure partway through leaves partial
    state (e.g. a MINOR user with no consent record). Not fixed here --
    would require new cross-call transaction machinery, a bigger
    architectural change than this sprint's scope.
    """
    if actor.account_type == AccountType.MINOR:
        raise AuthorizationError("Minor accounts cannot create child accounts.")

    get_household(household_id, db_path)
    _require_manager_membership(household_id, actor, db_path)

    child = create_user_account(username, email, password, account_type=AccountType.MINOR, db_path=db_path)
    add_member(actor, household_id, child.id, HouseholdRole.CHILD_LEARNER, db_path)
    relationship = create_guardian_child_relationship(
        actor.id, child.id, RelationshipStatus.ACTIVE, db_path
    )
    learning_profile = create_learning_profile(child.id, age_band, ai_coach_enabled=True, db_path=db_path)
    consent_record = grant_consent(
        actor, child.id, ConsentType.ACCOUNT_CREATION, policy_version, evidence, db_path
    )

    logger.info(
        "Guardian %d created child account %d in household %d", actor.id, child.id, household_id
    )

    return ChildAccountCreationResult(
        child=child,
        relationship=relationship,
        learning_profile=learning_profile,
        consent_record=consent_record,
    )


def list_children_for_guardian(
    actor: User, db_path: Path = DB_PATH
) -> list[tuple[User, GuardianChildRelationship]]:
    """Return a guardian's linked children (ACTIVE relationships only)."""
    relationships = list_relationships_for_guardian(actor.id, RelationshipStatus.ACTIVE, db_path)
    return [(get_user(relationship.child_user_id, db_path), relationship) for relationship in relationships]


def request_adult_transition(actor: User, db_path: Path = DB_PATH) -> User:
    """Self-initiated adult transition (no guardian-initiated variant is in
    ADR-007's API list). Flips account_type to ADULT and revokes every
    guardian relationship for this (former) child in the same call -- no
    partial/gradual cutover state (ADR-007 Age Transition Q2). Consent rows
    are left untouched as historical record (Q4/Q5) -- a fresh self-consent
    is a separate action the caller can now take via grant_consent(), since
    account_type is ADULT, but isn't forced as part of this action.
    """
    if actor.account_type == AccountType.ADULT:
        raise ValidationError("This account is already an adult account.")

    updated = update_account_type(actor.id, AccountType.ADULT, db_path)
    revoke_all_relationships_for_child(actor.id, db_path)

    logger.info("User %d completed self-initiated adult transition", actor.id)

    return updated
