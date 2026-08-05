from datetime import datetime, timezone

import pytest

from src.financial.consent.models import ConsentRecord, ConsentStatus, ConsentType

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _record(
    id: int = 1,
    subject_user_id: int = 2,
    consented_by_user_id: int | None = None,
    consent_type: ConsentType = ConsentType.ACCOUNT_CREATION,
    policy_version: str = "v1",
    status: ConsentStatus = ConsentStatus.GRANTED,
    evidence: str = "guardian confirmed via API request",
    created_at: datetime = NOW,
    granted_at: datetime | None = NOW,
    revoked_at: datetime | None = None,
) -> ConsentRecord:
    return ConsentRecord(
        id=id,
        subject_user_id=subject_user_id,
        consented_by_user_id=consented_by_user_id,
        consent_type=consent_type,
        policy_version=policy_version,
        status=status,
        evidence=evidence,
        created_at=created_at,
        granted_at=granted_at,
        revoked_at=revoked_at,
    )


def test_consent_record_rejects_empty_evidence():
    with pytest.raises(ValueError, match="Evidence cannot be empty"):
        _record(evidence="   ")


def test_consent_record_rejects_empty_policy_version():
    with pytest.raises(ValueError, match="Policy version cannot be empty"):
        _record(policy_version="")


def test_consent_record_rejects_non_positive_subject_id():
    with pytest.raises(ValueError, match="greater than zero"):
        _record(subject_user_id=0)


def test_consent_record_allows_none_consented_by_user_id():
    record = _record(consented_by_user_id=None)
    assert record.consented_by_user_id is None


def test_consent_record_to_dict_and_from_dict_round_trip():
    record = _record()
    assert ConsentRecord.from_dict(record.to_dict()) == record


def test_consent_record_revoke_shape_round_trip():
    record = _record(
        status=ConsentStatus.REVOKED, granted_at=None, revoked_at=NOW, consented_by_user_id=99
    )
    assert ConsentRecord.from_dict(record.to_dict()) == record
