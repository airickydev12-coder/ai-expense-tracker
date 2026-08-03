"""API schemas for recurring expense template endpoints."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.financial.recurring_expenses.models import RecurrenceFrequency
from src.financial.shared.categories import ExpenseCategory


class RecurringExpenseTemplateCreateRequest(BaseModel):
    """Request body for creating a recurring expense template."""

    name: str = Field(min_length=1)
    category: ExpenseCategory
    amount: Decimal = Field(ge=0)
    frequency: RecurrenceFrequency
    next_occurrence: date
    is_active: bool = True


class RecurringExpenseTemplateUpdateRequest(BaseModel):
    """Request body for updating a recurring expense template."""

    name: str | None = Field(default=None, min_length=1)
    category: ExpenseCategory | None = None
    amount: Decimal | None = Field(default=None, ge=0)
    frequency: RecurrenceFrequency | None = None
    next_occurrence: date | None = None
    is_active: bool | None = None


class RecurringExpenseTemplateResponse(BaseModel):
    """Serialized representation of a recurring expense template."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: ExpenseCategory
    amount: float
    frequency: RecurrenceFrequency
    next_occurrence: date
    is_active: bool


class GeneratedExpensesResponse(BaseModel):
    """Result of generating due expenses from recurring templates."""

    generated_count: int
    expense_ids: list[int]
