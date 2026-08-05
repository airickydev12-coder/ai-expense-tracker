from datetime import datetime, timezone
from pathlib import Path

from src.core.config import DB_PATH
from src.core.exceptions import AuthorizationError
from src.core.logging import get_logger
from src.financial.households.models import RelationshipStatus
from src.financial.households.repository import get_relationship
from src.financial.consent.models import ConsentRecord, ConsentStatus, ConsentType
from src.financial.consent.repository import create_consent_record
from src.financial.users.account_type import AccountType
from src.financial.users.models import User
from src.financial.users.service import get_user

logger = get_logger(__name__)


def _resolve_consenter(actor: User, subject: User, db_path: Path) -> int | None:
    """Return the consented_by_user_id to record: None for valid adult
    self-consent, actor.id for a valid active-guardian-for-child action --
    else raise AuthorizationError."""
    if subject.id == actor.id:
        if subject.account_type == AccountType.MINOR:
            raise AuthorizationError("Minors cannot grant or revoke their own consent.")
        return None

    if actor.account_type == AccountType.MINOR:
        raise AuthorizationError("Minor accounts cannot act as a consenter for another user.")

    relationship = get_relationship(actor.id, subject.id, db_path)
    if relationship is None or relationship.status != RelationshipStatus.ACTIVE:
        raise AuthorizationError("No active guardian relationship for this subject.")

    return actor.id


def grant_consent(
    actor: User,
    subject_user_id: int,
    consent_type: ConsentType,
    policy_version: str,
    evidence: str,
    db_path: Path = DB_PATH,
) -> ConsentRecord:
    """Record a consent grant, raising NotFoundError if the subject doesn't
    exist and AuthorizationError if the actor isn't allowed to consent for
    them (see _resolve_consenter)."""
    subject = get_user(subject_user_id, db_path)
    consented_by = _resolve_consenter(actor, subject, db_path)

    now = datetime.now(timezone.utc).isoformat()
    record = create_consent_record(
        subject.id,
        consented_by,
        consent_type,
        policy_version,
        ConsentStatus.GRANTED,
        evidence,
        granted_at=now,
        db_path=db_path,
    )

    logger.info(
        "Consent granted for subject %d (%s) by %s",
        subject.id,
        consent_type.value,
        "self" if consented_by is None else f"user {consented_by}",
    )

    return record


def revoke_consent(
    actor: User,
    subject_user_id: int,
    consent_type: ConsentType,
    policy_version: str,
    evidence: str,
    db_path: Path = DB_PATH,
) -> ConsentRecord:
    """Record a consent revocation. Same authorization rules as grant_consent."""
    subject = get_user(subject_user_id, db_path)
    consented_by = _resolve_consenter(actor, subject, db_path)

    now = datetime.now(timezone.utc).isoformat()
    record = create_consent_record(
        subject.id,
        consented_by,
        consent_type,
        policy_version,
        ConsentStatus.REVOKED,
        evidence,
        revoked_at=now,
        db_path=db_path,
    )

    logger.info(
        "Consent revoked for subject %d (%s) by %s",
        subject.id,
        consent_type.value,
        "self" if consented_by is None else f"user {consented_by}",
    )

    return record
