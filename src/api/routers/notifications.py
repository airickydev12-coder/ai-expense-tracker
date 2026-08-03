"""Notification API endpoints."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user
from src.api.schemas.notifications import (
    NotificationCheckResponse,
    NotificationLogEntryResponse,
)
from src.financial.notifications import service as notification_service
from src.financial.users.models import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/log", response_model=list[NotificationLogEntryResponse])
def get_notification_log(
    current_user: User = Depends(get_current_user),
) -> list[NotificationLogEntryResponse]:
    """Return the notification log, most recent first."""
    return [
        NotificationLogEntryResponse.model_validate(entry.to_dict())
        for entry in notification_service.get_notification_log(current_user.id)
    ]


@router.post("/check-now", response_model=NotificationCheckResponse)
def check_now(
    current_user: User = Depends(get_current_user),
) -> NotificationCheckResponse:
    """Run a notification check immediately, without waiting for the scheduled interval."""
    new_entries = notification_service.check_and_send_notifications(
        current_user.id, current_user.email
    )
    return NotificationCheckResponse(
        new_entry_count=len(new_entries),
        entries=[
            NotificationLogEntryResponse.model_validate(entry.to_dict())
            for entry in new_entries
        ],
    )
