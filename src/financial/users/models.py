from dataclasses import dataclass
from datetime import datetime

from src.core.exceptions import ValidationError
from src.financial.users.role import PlatformRole


@dataclass
class User:
    """Represents a registered application user."""

    id: int
    username: str
    email: str
    password_hash: str
    is_active: bool
    role: PlatformRole
    created_at: datetime
    updated_at: datetime
    email_verified_at: datetime | None = None
    mfa_enabled_at: datetime | None = None

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

    @property
    def email_verified(self) -> bool:
        """Whether the user has completed email verification."""
        return self.email_verified_at is not None

    @property
    def mfa_enabled(self) -> bool:
        """Whether the user has completed MFA enrollment and enabled it."""
        return self.mfa_enabled_at is not None

    def to_dict(self) -> dict:
        """Convert the user to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "is_active": int(self.is_active),
            "role": self.role.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "email_verified_at": (
                self.email_verified_at.isoformat() if self.email_verified_at else None
            ),
            "mfa_enabled_at": (
                self.mfa_enabled_at.isoformat() if self.mfa_enabled_at else None
            ),
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
            role=PlatformRole(data["role"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            email_verified_at=(
                datetime.fromisoformat(data["email_verified_at"])
                if data.get("email_verified_at")
                else None
            ),
            mfa_enabled_at=(
                datetime.fromisoformat(data["mfa_enabled_at"])
                if data.get("mfa_enabled_at")
                else None
            ),
        )
