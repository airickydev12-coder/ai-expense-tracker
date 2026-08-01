"""Expense API endpoints."""

from decimal import ROUND_HALF_UP

from fastapi import APIRouter, HTTPException, status

from src.api.schemas.analytics import (
    CategoryTotalResponse,
    ExpenseStatisticsResponse,
)
from src.api.schemas.expenses import (
    ExpenseCreateRequest,
    ExpenseResponse,
    ExpenseUpdateRequest,
)
from src.core.money import CURRENCY_PRECISION
from src.financial.expenses import analytics as expense_analytics
from src.financial.expenses import service as expense_service
from src.financial.expenses.models import Expense

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.get("/category-totals", response_model=list[CategoryTotalResponse])
def get_category_totals() -> list[CategoryTotalResponse]:
    """Return total spending grouped by expense category."""
    totals = expense_analytics.get_category_totals(expense_service.get_expenses())
    return [
        CategoryTotalResponse(category=category, total=total)
        for category, total in totals.items()
    ]


@router.get("/statistics", response_model=ExpenseStatisticsResponse)
def get_expense_statistics() -> ExpenseStatisticsResponse:
    """Return summary statistics for all recorded expenses."""
    expenses = expense_service.get_expenses()
    highest = expense_analytics.get_highest_expense(expenses)
    lowest = expense_analytics.get_lowest_expense(expenses)
    average = expense_analytics.get_average(expenses).quantize(
        CURRENCY_PRECISION,
        rounding=ROUND_HALF_UP,
    )
    return ExpenseStatisticsResponse(
        total=expense_analytics.get_total(expenses),
        average=average,
        highest=(
            ExpenseResponse.model_validate(highest) if highest is not None else None
        ),
        lowest=(ExpenseResponse.model_validate(lowest) if lowest is not None else None),
    )


@router.get("", response_model=list[ExpenseResponse])
def list_expenses() -> list[Expense]:
    """Return all recorded expenses."""
    return expense_service.get_expenses()


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int) -> ExpenseResponse:
    """Return an expense by ID."""
    expense = expense_service.get_expense_by_id(expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} was not found.",
        )
    return ExpenseResponse.model_validate(expense)


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(request: ExpenseCreateRequest) -> ExpenseResponse:
    """Create a new expense."""
    expense = expense_service.add_expense(
        name=request.name,
        category=request.category,
        amount=request.amount,
    )
    return ExpenseResponse.model_validate(expense)


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    request: ExpenseUpdateRequest,
) -> ExpenseResponse:
    """Update an existing expense."""
    if request.name is None and request.category is None and request.amount is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided.",
        )
    expense = expense_service.update_expense(
        expense_id=expense_id,
        name=request.name,
        category=request.category,
        amount=request.amount,
    )
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} was not found.",
        )
    return ExpenseResponse.model_validate(expense)


@router.delete("/{expense_id}", response_model=ExpenseResponse)
def delete_expense(expense_id: int) -> ExpenseResponse:
    """Delete and return an expense by ID."""
    expense = expense_service.delete_expense(expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} was not found.",
        )
    return ExpenseResponse.model_validate(expense)
