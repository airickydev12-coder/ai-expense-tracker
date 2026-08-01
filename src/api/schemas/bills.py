"""API schemas for bill endpoints."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BillCreateRequest(BaseModel):
    """Request body for creating a bill."""

    name: str = Field(min_length=1)
    amount: Decimal = Field(ge=0)
    due_day: int = Field(ge=1, le=31)
    is_paid: bool = False


class BillUpdateRequest(BaseModel):
    """Request body for updating a bill."""

    name: str | None = Field(default=None, min_length=1)
    amount: Decimal | None = Field(default=None, ge=0)
    due_day: int | None = Field(default=None, ge=1, le=31)
    is_paid: bool | None = None


class BillResponse(BaseModel):
    """Serialized representation of a bill."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    amount: float
    due_day: int
    is_paid: bool
