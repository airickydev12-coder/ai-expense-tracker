"""Pydantic schemas and API enums for recommendation endpoints."""

from enum import Enum

from pydantic import BaseModel


class RecommendationPriorityFilter(str, Enum):
    """Priority values accepted by recommendation query parameters."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationCategoryFilter(str, Enum):
    """Category values accepted by recommendation query parameters."""

    CASH_FLOW = "Cash Flow"
    BUDGET = "Budget"
    DEBT = "Debt"
    SAVINGS = "Savings"
    GOALS = "Goals"
    HEALTH = "Health"
    BILLS = "Bills"
    WEALTH = "Wealth"
    INCOME = "Income"
    EXPENSES = "Expenses"


class RecommendationResponse(BaseModel):
    """Serialized representation of a financial recommendation."""

    key: str
    priority: str
    category: str
    score: int
    title: str
    message: str
    action: str
    rationale: str
    source_rule: str
    is_actionable: bool
