import pytest

from src.core.exceptions import AuthorizationError, NotFoundError
from src.financial.consent import service as consent_service
from src.financial.consent.models import ConsentStatus, ConsentType
from src.financial.households.repository import create_guardian_child_relationship
from src.financial.households.models import RelationshipStatus
from src.financial.users import service as user_service
from src.financial.users.account_type import AccountType


def _make_user(db_path, username="alice", account_type=AccountType.ADULT):
    return user_service.create_user_account(
        username, f"{username}@example.com", "correct-password", account_type=account_type, db_path=db_path
    )


def test_grant_consent_self_for_adult(db_path):
    adult = _make_user(db_path)

    record = consent_service.grant_consent(
        adult, adult.id, ConsentType.DATA_COLLECTION, "v1", "checkbox confirmed", db_path
    )

    assert record.subject_user_id == adult.id
    assert record.consented_by_user_id is None
    assert record.status == ConsentStatus.GRANTED


def test_grant_consent_rejects_minor_self_consent(db_path):
    minor = _make_user(db_path, "kid", account_type=AccountType.MINOR)

    with pytest.raises(AuthorizationError):
        consent_service.grant_consent(
            minor, minor.id, ConsentType.DATA_COLLECTION, "v1", "evidence", db_path
        )


def test_grant_consent_for_child_by_active_guardian(db_path):
    guardian = _make_user(db_path, "guardian")
    child = _make_user(db_path, "child", account_type=AccountType.MINOR)
    create_guardian_child_relationship(guardian.id, child.id, RelationshipStatus.ACTIVE, db_path)

    record = consent_service.grant_consent(
        guardian, child.id, ConsentType.AI_COACH_USE, "v1", "guardian toggled on", db_path
    )

    assert record.subject_user_id == child.id
    assert record.consented_by_user_id == guardian.id


def test_grant_consent_rejects_guardian_without_active_relationship(db_path):
    guardian = _make_user(db_path, "guardian")
    child = _make_user(db_path, "child", account_type=AccountType.MINOR)

    with pytest.raises(AuthorizationError):
        consent_service.grant_consent(
            guardian, child.id, ConsentType.AI_COACH_USE, "v1", "evidence", db_path
        )


def test_grant_consent_rejects_revoked_guardian_relationship(db_path):
    guardian = _make_user(db_path, "guardian")
    child = _make_user(db_path, "child", account_type=AccountType.MINOR)
    create_guardian_child_relationship(guardian.id, child.id, RelationshipStatus.REVOKED, db_path)

    with pytest.raises(AuthorizationError):
        consent_service.grant_consent(
            guardian, child.id, ConsentType.AI_COACH_USE, "v1", "evidence", db_path
        )


def test_grant_consent_rejects_minor_acting_as_consenter_for_someone_else(db_path):
    minor = _make_user(db_path, "kid", account_type=AccountType.MINOR)
    other = _make_user(db_path, "other")

    with pytest.raises(AuthorizationError):
        consent_service.grant_consent(
            minor, other.id, ConsentType.DATA_COLLECTION, "v1", "evidence", db_path
        )


def test_grant_consent_raises_not_found_for_unknown_subject(db_path):
    adult = _make_user(db_path)

    with pytest.raises(NotFoundError):
        consent_service.grant_consent(
            adult, 999999, ConsentType.DATA_COLLECTION, "v1", "evidence", db_path
        )


def test_revoke_consent_writes_a_new_row_not_a_mutation(db_path):
    adult = _make_user(db_path)
    consent_service.grant_consent(adult, adult.id, ConsentType.MARKETING_COMMUNICATION, "v1", "opted in", db_path)

    revoked = consent_service.revoke_consent(
        adult, adult.id, ConsentType.MARKETING_COMMUNICATION, "v1", "opted out", db_path
    )

    from src.financial.consent.repository import list_consent_records_for_subject
    records = list_consent_records_for_subject(adult.id, db_path)

    assert len(records) == 2
    assert revoked.status == ConsentStatus.REVOKED
