"""Pydantic schemas for analytics endpoints."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer

from src.api.schemas.expenses import ExpenseResponse


class CategoryTotalResponse(BaseModel):
    """Total spending for a single expense category."""

    model_config = ConfigDict()

    category: str
    total: Decimal

    @field_serializer("total")
    def serialize_total(self, value: Decimal) -> float:
        return float(value)


class ExpenseStatisticsResponse(BaseModel):
    """Summary statistics for all recorded expenses."""

    model_config = ConfigDict()

    total: Decimal
    average: Decimal
    highest: ExpenseResponse | None
    lowest: ExpenseResponse | None

    @field_serializer("total", "average")
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)
