"""Pydantic schemas for the financial dashboard API."""

from pydantic import BaseModel, ConfigDict

from src.api.schemas.expenses import ExpenseResponse


class DashboardResponse(BaseModel):
    """Response schema for the financial dashboard."""

    model_config = ConfigDict(from_attributes=True)

    total_expenses: float
    average_expense: float
    highest_expense: ExpenseResponse | None
    lowest_expense: ExpenseResponse | None
    category_totals: dict[str, float]
    budget_count: int
    health_score: int
    health_status: str
