"""Pydantic schemas for recommendation endpoints."""

from pydantic import BaseModel


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
