from datetime import datetime, timezone

import pytest

from src.financial.notifications.models import NotificationLogEntry
from src.financial.notifications.repository import (
    load_notification_log_from_file,
    save_notification_log_to_file,
)


def test_save_and_load_notification_log(db_path):
    original_entries = [
        NotificationLogEntry(
            id=1,
            notification_key="bill_due:1:2026-09-01",
            channel="EMAIL",
            subject="Subject one",
            body="Body one",
            sent_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
            status="SENT",
        ),
        NotificationLogEntry(
            id=2,
            notification_key="budget_overrun:Food:2026-09-01",
            channel="EMAIL",
            subject="Subject two",
            body="Body two",
            sent_at=datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc),
            status="FAILED",
        ),
    ]

    save_notification_log_to_file(
        original_entries,
        db_path,
    )

    loaded_entries = load_notification_log_from_file(
        db_path,
    )

    assert loaded_entries == original_entries


def test_load_notification_log_returns_empty_list_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_notification_log.db"

    assert load_notification_log_from_file(db_path) == []


def test_save_notification_log_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "notification_log.db"

    entries = [
        NotificationLogEntry(
            id=1,
            notification_key="bill_due:1:2026-09-01",
            channel="EMAIL",
            subject="Subject",
            body="Body",
            sent_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
            status="SENT",
        )
    ]

    save_notification_log_to_file(
        entries,
        db_path,
    )

    assert db_path.exists()


def test_load_notification_log_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "notification_log.db"
    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load notification log",
    ):
        load_notification_log_from_file(db_path)
