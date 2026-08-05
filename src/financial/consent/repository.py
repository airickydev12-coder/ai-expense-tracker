import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.consent.models import ConsentRecord, ConsentStatus, ConsentType

logger = get_logger(__name__)

_COLUMNS = (
    "id, subject_user_id, consented_by_user_id, consent_type, policy_version, status, "
    "evidence, created_at, granted_at, revoked_at"
)


def create_consent_record(
    subject_user_id: int,
    consented_by_user_id: int | None,
    consent_type: ConsentType,
    policy_version: str,
    status: ConsentStatus,
    evidence: str,
    *,
    granted_at: str | None = None,
    revoked_at: str | None = None,
    db_path: Path = DB_PATH,
) -> ConsentRecord:
    """Insert a new, append-only consent record row.

    No update function exists for this table by design -- every grant or
    revoke action is its own new row (mirrors create_admin_audit_event's
    append-only shape), never mutated in place.
    """
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            cursor = connection.execute(
                "INSERT INTO consent_records "
                "(subject_user_id, consented_by_user_id, consent_type, policy_version, status, "
                "granted_at, revoked_at, evidence, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    subject_user_id,
                    consented_by_user_id,
                    consent_type.value,
                    policy_version,
                    status.value,
                    granted_at,
                    revoked_at,
                    evidence,
                    now,
                ),
            )
            record_id = cursor.lastrowid
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to create consent record in {db_path}") from error

    logger.debug(
        "Created consent record %d for subject %d (%s, %s) in %s",
        record_id,
        subject_user_id,
        consent_type.value,
        status.value,
        db_path,
    )

    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                f"SELECT {_COLUMNS} FROM consent_records WHERE id = ?", (record_id,)
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to reload consent record {record_id} from {db_path}") from error

    if row is None:
        raise PersistenceError(f"Failed to reload newly created consent record in {db_path}")
    return ConsentRecord.from_dict(dict(row))


def get_latest_consent_record(
    subject_user_id: int, consent_type: ConsentType, db_path: Path = DB_PATH
) -> ConsentRecord | None:
    """Return the most recent consent record for a (subject, type) pair.

    "Current status" for a consent pair is the most recent row, since this
    table is append-only -- never mutated in place.
    """
    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                f"SELECT {_COLUMNS} FROM consent_records "
                "WHERE subject_user_id = ? AND consent_type = ? ORDER BY id DESC LIMIT 1",
                (subject_user_id, consent_type.value),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load latest consent record from {db_path}") from error

    return ConsentRecord.from_dict(dict(row)) if row is not None else None


def list_consent_records_for_subject(
    subject_user_id: int, db_path: Path = DB_PATH
) -> list[ConsentRecord]:
    """Return every consent record for a subject, oldest first."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                f"SELECT {_COLUMNS} FROM consent_records WHERE subject_user_id = ? ORDER BY id",
                (subject_user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to load consent records for subject {subject_user_id} from {db_path}"
        ) from error

    return [ConsentRecord.from_dict(dict(row)) for row in rows]
