from dataclasses import dataclass
from datetime import datetime

from src.core.exceptions import ValidationError


@dataclass
class NotificationLogEntry:
    """Represents one attempted (sent or failed) notification delivery."""

    id: int
    notification_key: str
    channel: str
    subject: str
    body: str
    sent_at: datetime
    status: str

    def __post_init__(self) -> None:
        """Validate the log entry after initialization."""
        if self.id <= 0:
            raise ValidationError("Notification log entry ID must be greater than zero.")

        if not self.notification_key.strip():
            raise ValidationError("Notification key cannot be empty.")

        if not self.channel.strip():
            raise ValidationError("Notification channel cannot be empty.")

        if self.status not in {"SENT", "FAILED"}:
            raise ValidationError("Notification status must be 'SENT' or 'FAILED'.")

    def to_dict(self) -> dict:
        """Convert the log entry to a dictionary for storage."""
        return {
            "id": self.id,
            "notification_key": self.notification_key,
            "channel": self.channel,
            "subject": self.subject,
            "body": self.body,
            "sent_at": self.sent_at.isoformat(),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NotificationLogEntry":
        """Create a NotificationLogEntry from a dictionary."""
        return cls(
            id=int(data["id"]),
            notification_key=str(data["notification_key"]),
            channel=str(data["channel"]),
            subject=str(data["subject"]),
            body=str(data["body"]),
            sent_at=datetime.fromisoformat(str(data["sent_at"])),
            status=str(data["status"]),
        )
