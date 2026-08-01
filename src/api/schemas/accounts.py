"""API schemas for account endpoints."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AccountCreateRequest(BaseModel):
    """Request body for creating an account."""

    name: str = Field(min_length=1)
    account_type: str = Field(min_length=1)
    balance: Decimal


class AccountUpdateRequest(BaseModel):
    """Request body for updating an account."""

    name: str | None = Field(default=None, min_length=1)
    account_type: str | None = Field(default=None, min_length=1)
    balance: Decimal | None = None


class AccountResponse(BaseModel):
    """Serialized representation of an account."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    account_type: str
    balance: float
