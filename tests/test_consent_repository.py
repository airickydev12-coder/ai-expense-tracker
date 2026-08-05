from src.financial.consent.models import ConsentStatus, ConsentType
from src.financial.consent.repository import (
    create_consent_record,
    get_latest_consent_record,
    list_consent_records_for_subject,
)


def test_create_consent_record_round_trips(db_path):
    record = create_consent_record(
        1, 2, ConsentType.ACCOUNT_CREATION, "v1", ConsentStatus.GRANTED, "evidence text",
        granted_at="2026-01-01T00:00:00+00:00", db_path=db_path,
    )

    assert record.subject_user_id == 1
    assert record.consented_by_user_id == 2
    assert record.status == ConsentStatus.GRANTED
    assert record.granted_at is not None
    assert record.revoked_at is None


def test_grant_then_revoke_is_append_only_not_mutated(db_path):
    create_consent_record(
        1, None, ConsentType.DATA_COLLECTION, "v1", ConsentStatus.GRANTED, "self-granted",
        granted_at="2026-01-01T00:00:00+00:00", db_path=db_path,
    )
    create_consent_record(
        1, None, ConsentType.DATA_COLLECTION, "v1", ConsentStatus.REVOKED, "self-revoked",
        revoked_at="2026-01-02T00:00:00+00:00", db_path=db_path,
    )

    records = list_consent_records_for_subject(1, db_path)

    assert len(records) == 2
    assert records[0].status == ConsentStatus.GRANTED
    assert records[1].status == ConsentStatus.REVOKED


def test_get_latest_consent_record_returns_most_recent_by_id(db_path):
    create_consent_record(
        1, None, ConsentType.AI_COACH_USE, "v1", ConsentStatus.GRANTED, "granted",
        granted_at="2026-01-01T00:00:00+00:00", db_path=db_path,
    )
    create_consent_record(
        1, None, ConsentType.AI_COACH_USE, "v2", ConsentStatus.REVOKED, "revoked",
        revoked_at="2026-01-02T00:00:00+00:00", db_path=db_path,
    )

    latest = get_latest_consent_record(1, ConsentType.AI_COACH_USE, db_path)

    assert latest is not None
    assert latest.status == ConsentStatus.REVOKED
    assert latest.policy_version == "v2"


def test_get_latest_consent_record_returns_none_when_missing(db_path):
    assert get_latest_consent_record(1, ConsentType.MARKETING_COMMUNICATION, db_path) is None


def test_list_consent_records_for_subject_scoped_by_subject(db_path):
    create_consent_record(
        1, None, ConsentType.ACCOUNT_CREATION, "v1", ConsentStatus.GRANTED, "evidence",
        granted_at="2026-01-01T00:00:00+00:00", db_path=db_path,
    )
    create_consent_record(
        2, None, ConsentType.ACCOUNT_CREATION, "v1", ConsentStatus.GRANTED, "evidence",
        granted_at="2026-01-01T00:00:00+00:00", db_path=db_path,
    )

    assert len(list_consent_records_for_subject(1, db_path)) == 1
    assert len(list_consent_records_for_subject(2, db_path)) == 1
