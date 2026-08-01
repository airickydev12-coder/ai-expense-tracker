from dataclasses import dataclass
from datetime import datetime, timezone

from src.core.exceptions import ValidationError
from src.financial.recommendations.status import RecommendationStatus


@dataclass
class RecommendationRecord:
    """Tracks the lifecycle state of one recommendation."""

    recommendation_key: str
    status: RecommendationStatus
    created_at: datetime
    updated_at: datetime
    note: str = ""

    def __post_init__(self) -> None:
        """Normalize and validate record fields."""
        self.recommendation_key = self.recommendation_key.strip()
        self.note = self.note.strip()

        if not self.recommendation_key:
            raise ValidationError(
                "Recommendation key cannot be empty."
            )

        if self.updated_at < self.created_at:
            raise ValidationError(
                "Updated timestamp cannot be earlier than created timestamp."
            )

    @classmethod
    def create(
        cls,
        recommendation_key: str,
        status: RecommendationStatus = RecommendationStatus.NEW,
        note: str = "",
    ) -> "RecommendationRecord":
        """Create a new lifecycle record."""
        timestamp = datetime.now(timezone.utc)

        return cls(
            recommendation_key=recommendation_key,
            status=status,
            created_at=timestamp,
            updated_at=timestamp,
            note=note,
        )

    def update_status(
        self,
        status: RecommendationStatus,
        note: str = "",
    ) -> None:
        """Update the record status and timestamp."""
        self.status = status
        self.updated_at = datetime.now(timezone.utc)

        if note:
            self.note = note.strip()

    def to_dict(self) -> dict:
        """Convert the record to a dictionary."""
        return {
            "recommendation_key": self.recommendation_key,
            "status": self.status.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "note": self.note,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> "RecommendationRecord":
        """Create a lifecycle record from a dictionary."""
        return cls(
            recommendation_key=str(
                data["recommendation_key"]
            ),
            status=RecommendationStatus[
                str(data["status"])
            ],
            created_at=datetime.fromisoformat(
                str(data["created_at"])
            ),
            updated_at=datetime.fromisoformat(
                str(data["updated_at"])
            ),
            note=str(data.get("note", "")),
        )