from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.core.exceptions import ValidationError


class HouseholdRole(str, Enum):
    """A user's role within one specific household membership -- per
    membership, not per user, since an adult can belong to more than one
    household. See ADR-007."""

    OWNER = "owner"
    GUARDIAN = "guardian"
    ADULT_MEMBER = "adult_member"
    CHILD_LEARNER = "child_learner"


class RelationshipStatus(str, Enum):
    """Current state of one (guardian, child) relationship row -- mutated
    in place, not append-only (see ConsentRecord for the append-only
    equivalent used for consent actions)."""

    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"


class AgeBand(str, Enum):
    """A minor's age band for content-banding purposes -- never an exact
    birthdate (data-minimization choice, see ADR-007). Member names are
    identifier-safe; values are the hyphenated band strings."""

    AGE_6_9 = "6-9"
    AGE_10_13 = "10-13"
    AGE_14_17 = "14-17"


@dataclass
class Household:
    """A household grouping guardians, adult members, and child learners.

    Deliberately has no owner_user_id column/field -- ownership is derived
    from the one HouseholdMembership row with household_role=OWNER, not
    duplicated here (see ADR-007).
    """

    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValidationError("Household ID must be greater than zero.")

        if not self.name.strip():
            raise ValidationError("Household name cannot be empty.")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Household":
        return cls(
            id=int(data["id"]),
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class HouseholdMembership:
    """One user's membership row in one household. Composite (household_id,
    user_id) primary key -- a user can only hold one role per household."""

    household_id: int
    user_id: int
    household_role: HouseholdRole
    joined_at: datetime

    def __post_init__(self) -> None:
        if self.household_id <= 0:
            raise ValidationError("Household ID must be greater than zero.")

        if self.user_id <= 0:
            raise ValidationError("User ID must be greater than zero.")

        if not isinstance(self.household_role, HouseholdRole):
            self.household_role = HouseholdRole(self.household_role)

    def to_dict(self) -> dict:
        return {
            "household_id": self.household_id,
            "user_id": self.user_id,
            "household_role": self.household_role.value,
            "joined_at": self.joined_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HouseholdMembership":
        return cls(
            household_id=int(data["household_id"]),
            user_id=int(data["user_id"]),
            household_role=HouseholdRole(data["household_role"]),
            joined_at=datetime.fromisoformat(data["joined_at"]),
        )


@dataclass
class GuardianChildRelationship:
    """A direct, explicit (guardian, child) relationship -- deliberately
    separate from household co-membership, since a non-custodial guardian
    may need visibility into a child outside their household. Status
    mutates in place (current relationship state, not a log). See
    ADR-007."""

    id: int
    guardian_user_id: int
    child_user_id: int
    status: RelationshipStatus
    created_at: datetime
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValidationError("Relationship ID must be greater than zero.")

        if self.guardian_user_id <= 0:
            raise ValidationError("Guardian user ID must be greater than zero.")

        if self.child_user_id <= 0:
            raise ValidationError("Child user ID must be greater than zero.")

        if not isinstance(self.status, RelationshipStatus):
            self.status = RelationshipStatus(self.status)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "guardian_user_id": self.guardian_user_id,
            "child_user_id": self.child_user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GuardianChildRelationship":
        return cls(
            id=int(data["id"]),
            guardian_user_id=int(data["guardian_user_id"]),
            child_user_id=int(data["child_user_id"]),
            status=RelationshipStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            revoked_at=(
                datetime.fromisoformat(data["revoked_at"]) if data.get("revoked_at") else None
            ),
        )


@dataclass
class LearningProfile:
    """A MINOR account's learning-domain profile -- user_id is the primary
    key (genuinely 1:1, unlike every other table's surrogate id).
    ai_coach_enabled is the guardian-facing kill switch for the AI coach;
    the actual AI policy design is a separate, not-yet-built item. See
    ADR-007."""

    user_id: int
    age_band: AgeBand
    ai_coach_enabled: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.user_id <= 0:
            raise ValidationError("User ID must be greater than zero.")

        if not isinstance(self.age_band, AgeBand):
            self.age_band = AgeBand(self.age_band)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "age_band": self.age_band.value,
            "ai_coach_enabled": int(self.ai_coach_enabled),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LearningProfile":
        return cls(
            user_id=int(data["user_id"]),
            age_band=AgeBand(data["age_band"]),
            ai_coach_enabled=bool(data["ai_coach_enabled"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
