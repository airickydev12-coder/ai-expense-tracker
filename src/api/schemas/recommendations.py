"""Pydantic schemas and API enums for recommendation endpoints."""

from enum import Enum

from pydantic import BaseModel


class RecommendationPriorityFilter(str, Enum):
    """Priority values accepted by recommendation query parameters."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationPriorityResponse(BaseModel):
    """Priority metadata returned by the recommendation API."""

    name: str
    value: int
    score: int


class RecommendationCategoryResponse(BaseModel):
    """Category metadata returned by the recommendation API."""

    name: str
    value: str


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


class RecommendationActionRequest(BaseModel):
    """Request body for a recommendation lifecycle action."""

    note: str = ""


class RecommendationRecordResponse(BaseModel):
    """Serialized representation of a recommendation's lifecycle record."""

    recommendation_key: str
    status: str
    created_at: str
    updated_at: str
    note: str
