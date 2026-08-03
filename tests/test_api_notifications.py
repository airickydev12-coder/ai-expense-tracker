"""Tests for the notification API endpoints."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.notifications.models import NotificationLogEntry
from src.financial.notifications.service import notification_log

client = TestClient(app)


def setup_function() -> None:
    """Clear notification log state before each test."""
    notification_log.clear()


def test_get_notification_log_returns_empty_list() -> None:
    response = client.get("/notifications/log")

    assert response.status_code == 200
    assert response.json() == []


def test_get_notification_log_returns_entries_most_recent_first() -> None:
    notification_log.append(
        NotificationLogEntry(
            id=1,
            notification_key="a",
            channel="EMAIL",
            subject="Older",
            body="Older body",
            sent_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            status="SENT",
        )
    )
    notification_log.append(
        NotificationLogEntry(
            id=2,
            notification_key="b",
            channel="EMAIL",
            subject="Newer",
            body="Newer body",
            sent_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            status="FAILED",
        )
    )

    response = client.get("/notifications/log")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["subject"] == "Newer"
    assert body[0]["status"] == "FAILED"
    assert body[1]["subject"] == "Older"


def test_check_now_returns_no_new_entries_when_nothing_actionable() -> None:
    response = client.post("/notifications/check-now")

    assert response.status_code == 200
    body = response.json()
    assert body["new_entry_count"] == 0
    assert body["entries"] == []
