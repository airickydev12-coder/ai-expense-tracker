"""API schemas for notification endpoints."""

from pydantic import BaseModel


class NotificationLogEntryResponse(BaseModel):
    """Serialized representation of one notification log entry."""

    id: int
    notification_key: str
    channel: str
    subject: str
    body: str
    sent_at: str
    status: str


class NotificationCheckResponse(BaseModel):
    """Result of an on-demand notification check."""

    new_entry_count: int
    entries: list[NotificationLogEntryResponse]
