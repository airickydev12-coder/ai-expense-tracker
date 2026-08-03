from dataclasses import dataclass
from datetime import datetime

from src.core.exceptions import ValidationError


@dataclass
class User:
    """Represents a registered application user."""

    id: int
    username: str
    email: str
    password_hash: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate the user after initialization."""
        if self.id <= 0:
            raise ValidationError("User ID must be greater than zero.")

        if not self.username.strip():
            raise ValidationError("Username cannot be empty.")

        if "@" not in self.email:
            raise ValidationError("Email must be a valid email address.")

        if not self.password_hash.strip():
            raise ValidationError("Password hash cannot be empty.")

    def to_dict(self) -> dict:
        """Convert the user to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "is_active": int(self.is_active),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create a User from a dictionary."""
        return cls(
            id=int(data["id"]),
            username=data["username"],
            email=data["email"],
            password_hash=data["password_hash"],
            is_active=bool(data["is_active"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
