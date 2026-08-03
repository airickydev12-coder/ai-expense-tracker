"""Tests for the notification API endpoints."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.notifications.models import NotificationLogEntry
from src.financial.notifications.service import notification_log

client = TestClient(app)
current_user_id: int | None = None


@pytest.fixture(autouse=True)
def _authenticate() -> None:
    """Register and log in a throwaway user, authenticating `client` for every test."""
    global current_user_id

    register_response = client.post(
        "/auth/register",
        json={"username": "testuser", "email": "testuser@example.com", "password": "correct-password"},
    )
    current_user_id = register_response.json()["id"]

    token = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "correct-password"},
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"


def setup_function() -> None:
    """Clear notification log state before each test."""
    notification_log.clear()


def test_get_notification_log_returns_empty_list() -> None:
    response = client.get("/notifications/log")

    assert response.status_code == 200
    assert response.json() == []


def test_get_notification_log_returns_entries_most_recent_first() -> None:
    notification_log[current_user_id] = [
        NotificationLogEntry(
            id=1,
            notification_key="a",
            channel="EMAIL",
            subject="Older",
            body="Older body",
            sent_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            status="SENT",
        ),
        NotificationLogEntry(
            id=2,
            notification_key="b",
            channel="EMAIL",
            subject="Newer",
            body="Newer body",
            sent_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            status="FAILED",
        ),
    ]

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
