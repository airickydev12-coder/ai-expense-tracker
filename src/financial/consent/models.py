from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.core.exceptions import ValidationError


class ConsentType(str, Enum):
    """What kind of consent this record represents. Not exhaustive -- extend
    as new consent-gated features are added. See ADR-007."""

    ACCOUNT_CREATION = "account_creation"
    DATA_COLLECTION = "data_collection"
    AI_COACH_USE = "ai_coach_use"
    MARKETING_COMMUNICATION = "marketing_communication"


class ConsentStatus(str, Enum):
    """Whether one consent event was a grant or a revoke."""

    GRANTED = "granted"
    REVOKED = "revoked"


@dataclass
class ConsentRecord:
    """One append-only consent event -- a new row per grant or revoke
    action, never mutated in place (mirrors admin_audit_events' pattern).
    Current status for a (subject_user_id, consent_type) pair is the most
    recent row by id/created_at.

    subject_user_id + nullable consented_by_user_id (not minor_user_id +
    guardian_user_id) supports both guardian-consents-for-minor and adult
    self-consent with the same table/vocabulary --
    consented_by_user_id IS NULL means the subject consented for
    themselves. See ADR-007.
    """

    id: int
    subject_user_id: int
    consented_by_user_id: int | None
    consent_type: ConsentType
    policy_version: str
    status: ConsentStatus
    evidence: str
    created_at: datetime
    granted_at: datetime | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValidationError("Consent record ID must be greater than zero.")

        if self.subject_user_id <= 0:
            raise ValidationError("Subject user ID must be greater than zero.")

        if self.consented_by_user_id is not None and self.consented_by_user_id <= 0:
            raise ValidationError("Consented-by user ID must be greater than zero.")

        if not self.policy_version.strip():
            raise ValidationError("Policy version cannot be empty.")

        if not self.evidence.strip():
            raise ValidationError("Evidence cannot be empty.")

        if not isinstance(self.consent_type, ConsentType):
            self.consent_type = ConsentType(self.consent_type)

        if not isinstance(self.status, ConsentStatus):
            self.status = ConsentStatus(self.status)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subject_user_id": self.subject_user_id,
            "consented_by_user_id": self.consented_by_user_id,
            "consent_type": self.consent_type.value,
            "policy_version": self.policy_version,
            "status": self.status.value,
            "evidence": self.evidence,
            "created_at": self.created_at.isoformat(),
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConsentRecord":
        return cls(
            id=int(data["id"]),
            subject_user_id=int(data["subject_user_id"]),
            consented_by_user_id=(
                int(data["consented_by_user_id"])
                if data.get("consented_by_user_id") is not None
                else None
            ),
            consent_type=ConsentType(data["consent_type"]),
            policy_version=data["policy_version"],
            status=ConsentStatus(data["status"]),
            evidence=data["evidence"],
            created_at=datetime.fromisoformat(data["created_at"]),
            granted_at=(
                datetime.fromisoformat(data["granted_at"]) if data.get("granted_at") else None
            ),
            revoked_at=(
                datetime.fromisoformat(data["revoked_at"]) if data.get("revoked_at") else None
            ),
        )
