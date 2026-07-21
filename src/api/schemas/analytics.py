"""Pydantic schemas for analytics endpoints."""

from src.api.schemas.expenses import ExpenseResponse
from pydantic import BaseModel


class CategoryTotalResponse(BaseModel):
    """Total spending for a single expense category."""

    category: str
    total: float


class ExpenseStatisticsResponse(BaseModel):
    """Summary statistics for all recorded expenses."""

    total: float
    average: float
    highest: ExpenseResponse | None
    lowest: ExpenseResponse | None
