"""API schemas for expense endpoints."""

from pydantic import BaseModel, ConfigDict, Field

from src.financial.shared.categories import ExpenseCategory


class ExpenseCreateRequest(BaseModel):
    """Request body for creating an expense."""

    name: str = Field(min_length=1)
    category: ExpenseCategory
    amount: float = Field(ge=0)


class ExpenseUpdateRequest(BaseModel):
    """Request body for updating an expense."""

    name: str | None = Field(default=None, min_length=1)
    category: ExpenseCategory | None = None
    amount: float | None = Field(default=None, ge=0)


class ExpenseResponse(BaseModel):
    """Serialized representation of an expense."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: ExpenseCategory
    amount: float
