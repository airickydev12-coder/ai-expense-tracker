"""Pydantic schemas for budget API requests and responses."""

from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from src.financial.shared.categories import ExpenseCategory


class BudgetCreateRequest(BaseModel):
    """Request body for creating or replacing a category budget."""

    category: ExpenseCategory
    limit: Decimal = Field(gt=0)


class BudgetUpdateRequest(BaseModel):
    """Request body for updating a category budget."""

    limit: Decimal = Field(gt=0)


class BudgetResponse(BaseModel):
    """Serialized budget returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    category: ExpenseCategory
    limit: float
