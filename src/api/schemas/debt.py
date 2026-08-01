"""API schemas for debt endpoints."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DebtCreateRequest(BaseModel):
    """Request body for creating a debt."""

    name: str = Field(min_length=1)
    balance: Decimal = Field(ge=0)
    interest_rate: float = Field(ge=0)
    minimum_payment: Decimal = Field(ge=0)


class DebtUpdateRequest(BaseModel):
    """Request body for updating a debt."""

    name: str | None = Field(default=None, min_length=1)
    balance: Decimal | None = Field(default=None, ge=0)
    interest_rate: float | None = Field(default=None, ge=0)
    minimum_payment: Decimal | None = Field(default=None, ge=0)


class DebtPaymentRequest(BaseModel):
    """Request body for applying a payment to a debt."""

    payment: Decimal


class DebtResponse(BaseModel):
    """Serialized representation of a debt."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    balance: float
    interest_rate: float
    minimum_payment: float
