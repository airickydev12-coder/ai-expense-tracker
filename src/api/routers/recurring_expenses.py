"""Recurring expense template API endpoints."""

from fastapi import APIRouter, HTTPException, status

from src.api.schemas.recurring_expenses import (
    GeneratedExpensesResponse,
    RecurringExpenseTemplateCreateRequest,
    RecurringExpenseTemplateResponse,
    RecurringExpenseTemplateUpdateRequest,
)
from src.financial.recurring_expenses import service as recurring_expense_service
from src.financial.recurring_expenses.models import RecurringExpenseTemplate

router = APIRouter(prefix="/recurring-expenses", tags=["Recurring Expenses"])


@router.get("", response_model=list[RecurringExpenseTemplateResponse])
def list_recurring_expense_templates() -> list[RecurringExpenseTemplate]:
    """Return all recurring expense templates."""
    return recurring_expense_service.get_recurring_expense_templates()


@router.get("/{template_id}", response_model=RecurringExpenseTemplateResponse)
def get_recurring_expense_template(template_id: int) -> RecurringExpenseTemplateResponse:
    """Return a recurring expense template by ID."""
    template = recurring_expense_service.get_recurring_expense_template_by_id(template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring expense template with ID {template_id} was not found.",
        )
    return RecurringExpenseTemplateResponse.model_validate(template)


@router.post(
    "",
    response_model=RecurringExpenseTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_recurring_expense_template(
    request: RecurringExpenseTemplateCreateRequest,
) -> RecurringExpenseTemplateResponse:
    """Create a new recurring expense template."""
    template = recurring_expense_service.add_recurring_expense_template(
        name=request.name,
        category=request.category,
        amount=request.amount,
        frequency=request.frequency,
        next_occurrence=request.next_occurrence,
        is_active=request.is_active,
    )
    return RecurringExpenseTemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=RecurringExpenseTemplateResponse)
def update_recurring_expense_template(
    template_id: int,
    request: RecurringExpenseTemplateUpdateRequest,
) -> RecurringExpenseTemplateResponse:
    """Update an existing recurring expense template."""
    if (
        request.name is None
        and request.category is None
        and request.amount is None
        and request.frequency is None
        and request.next_occurrence is None
        and request.is_active is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided.",
        )
    template = recurring_expense_service.update_recurring_expense_template(
        template_id=template_id,
        name=request.name,
        category=request.category,
        amount=request.amount,
        frequency=request.frequency,
        next_occurrence=request.next_occurrence,
        is_active=request.is_active,
    )
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring expense template with ID {template_id} was not found.",
        )
    return RecurringExpenseTemplateResponse.model_validate(template)


@router.delete("/{template_id}", response_model=RecurringExpenseTemplateResponse)
def delete_recurring_expense_template(template_id: int) -> RecurringExpenseTemplateResponse:
    """Delete and return a recurring expense template by ID."""
    template = recurring_expense_service.delete_recurring_expense_template(template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring expense template with ID {template_id} was not found.",
        )
    return RecurringExpenseTemplateResponse.model_validate(template)


@router.post("/generate", response_model=GeneratedExpensesResponse)
def generate_due_expenses() -> GeneratedExpensesResponse:
    """Generate real expenses for every active template that is due."""
    generated = recurring_expense_service.generate_due_expenses()
    return GeneratedExpensesResponse(
        generated_count=len(generated),
        expense_ids=[expense.id for expense in generated],
    )
