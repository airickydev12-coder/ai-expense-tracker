from enum import IntEnum


class RecommendationPriority(IntEnum):
    """Priority levels for financial recommendations."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
