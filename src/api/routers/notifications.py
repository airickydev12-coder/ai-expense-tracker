"""Notification API endpoints."""

from fastapi import APIRouter

from src.api.schemas.notifications import (
    NotificationCheckResponse,
    NotificationLogEntryResponse,
)
from src.financial.notifications import service as notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/log", response_model=list[NotificationLogEntryResponse])
def get_notification_log() -> list[NotificationLogEntryResponse]:
    """Return the notification log, most recent first."""
    return [
        NotificationLogEntryResponse.model_validate(entry.to_dict())
        for entry in notification_service.get_notification_log()
    ]


@router.post("/check-now", response_model=NotificationCheckResponse)
def check_now() -> NotificationCheckResponse:
    """Run a notification check immediately, without waiting for the scheduled interval."""
    new_entries = notification_service.check_and_send_notifications()
    return NotificationCheckResponse(
        new_entry_count=len(new_entries),
        entries=[
            NotificationLogEntryResponse.model_validate(entry.to_dict())
            for entry in new_entries
        ],
    )
