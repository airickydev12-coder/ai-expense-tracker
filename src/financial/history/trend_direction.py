from enum import Enum


class TrendDirection(Enum):
    """Direction of change for a financial metric."""

    IMPROVING = "Improving"
    DECLINING = "Declining"
    STABLE = "Stable"
    INSUFFICIENT_DATA = "Insufficient Data"


class FinancialMomentum(Enum):
    """Overall direction of the user's financial position."""

    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    STABLE = "Stable"
    INSUFFICIENT_DATA = "Insufficient Data"