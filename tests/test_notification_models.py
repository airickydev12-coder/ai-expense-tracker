from datetime import datetime, timezone

import pytest

from src.financial.notifications.models import NotificationLogEntry


def test_notification_log_entry_creation():
    entry = NotificationLogEntry(
        id=1,
        notification_key="bill_due:1:2026-09-01",
        channel="EMAIL",
        subject="Financial Tracker: 1 item(s) need your attention",
        body="Bill due soon: Electric ($125.00, due day 15)",
        sent_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        status="SENT",
    )

    assert entry.notification_key == "bill_due:1:2026-09-01"
    assert entry.channel == "EMAIL"
    assert entry.status == "SENT"


def test_invalid_id():
    with pytest.raises(ValueError):
        NotificationLogEntry(
            id=0,
            notification_key="bill_due:1:2026-09-01",
            channel="EMAIL",
            subject="Subject",
            body="Body",
            sent_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
            status="SENT",
        )


def test_empty_notification_key():
    with pytest.raises(ValueError):
        NotificationLogEntry(
            id=1,
            notification_key="   ",
            channel="EMAIL",
            subject="Subject",
            body="Body",
            sent_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
            status="SENT",
        )


def test_invalid_status():
    with pytest.raises(ValueError):
        NotificationLogEntry(
            id=1,
            notification_key="bill_due:1:2026-09-01",
            channel="EMAIL",
            subject="Subject",
            body="Body",
            sent_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
            status="PENDING",
        )


def test_to_dict_and_from_dict_round_trip():
    entry = NotificationLogEntry(
        id=1,
        notification_key="bill_due:1:2026-09-01",
        channel="EMAIL",
        subject="Subject",
        body="Body",
        sent_at=datetime(2026, 9, 1, 12, 30, tzinfo=timezone.utc),
        status="FAILED",
    )

    restored = NotificationLogEntry.from_dict(entry.to_dict())

    assert restored == entry
