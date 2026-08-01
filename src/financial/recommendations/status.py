from enum import Enum


class RecommendationStatus(Enum):
    """Lifecycle states for financial recommendations."""

    NEW = "New"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    DISMISSED = "Dismissed"
    SUPPRESSED = "Suppressed"
