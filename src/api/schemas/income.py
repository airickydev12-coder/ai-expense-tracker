"""API schemas for income endpoints."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class IncomeCreateRequest(BaseModel):
    """Request body for creating an income entry."""

    source: str = Field(min_length=1)
    amount: Decimal = Field(ge=0)


class IncomeUpdateRequest(BaseModel):
    """Request body for updating an income entry."""

    source: str | None = Field(default=None, min_length=1)
    amount: Decimal | None = Field(default=None, ge=0)


class IncomeResponse(BaseModel):
    """Serialized representation of an income entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    amount: float
