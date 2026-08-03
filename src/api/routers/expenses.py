"""Expense API endpoints."""

from decimal import ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.dependencies import get_current_user
from src.api.schemas.analytics import (
    CategoryTotalResponse,
    ExpenseStatisticsResponse,
)
from src.api.schemas.expenses import (
    ExpenseCategorySuggestionRequest,
    ExpenseCategorySuggestionResponse,
    ExpenseCreateRequest,
    ExpenseResponse,
    ExpenseUpdateRequest,
)
from src.core.money import CURRENCY_PRECISION
from src.financial.expenses import analytics as expense_analytics
from src.financial.expenses import categorization as expense_categorization
from src.financial.expenses import service as expense_service
from src.financial.expenses.export import export_expenses_to_csv
from src.financial.expenses.models import Expense
from src.financial.users.models import User

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.get("/category-totals", response_model=list[CategoryTotalResponse])
def get_category_totals(
    current_user: User = Depends(get_current_user),
) -> list[CategoryTotalResponse]:
    """Return total spending grouped by expense category."""
    totals = expense_analytics.get_category_totals(
        expense_service.get_expenses(current_user.id)
    )
    return [
        CategoryTotalResponse(category=category, total=total)
        for category, total in totals.items()
    ]


@router.get("/statistics", response_model=ExpenseStatisticsResponse)
def get_expense_statistics(
    current_user: User = Depends(get_current_user),
) -> ExpenseStatisticsResponse:
    """Return summary statistics for all recorded expenses."""
    expenses = expense_service.get_expenses(current_user.id)
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


@router.get("/export")
def export_expenses(
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Return all recorded expenses as a downloadable CSV file."""
    csv_text = export_expenses_to_csv(expense_service.get_expenses(current_user.id))
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"},
    )


@router.post(
    "/suggest-category",
    response_model=ExpenseCategorySuggestionResponse,
)
def suggest_expense_category(
    request: ExpenseCategorySuggestionRequest,
    current_user: User = Depends(get_current_user),
) -> ExpenseCategorySuggestionResponse:
    """Suggest an expense category for the given name using Claude."""
    category = expense_categorization.suggest_category(request.name)
    return ExpenseCategorySuggestionResponse(category=category)


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(current_user: User = Depends(get_current_user)) -> list[Expense]:
    """Return all recorded expenses."""
    return expense_service.get_expenses(current_user.id)


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Return an expense by ID."""
    expense = expense_service.get_expense_by_id(current_user.id, expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} was not found.",
        )
    return ExpenseResponse.model_validate(expense)


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    request: ExpenseCreateRequest,
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Create a new expense."""
    expense = expense_service.add_expense(
        user_id=current_user.id,
        name=request.name,
        category=request.category,
        amount=request.amount,
    )
    return ExpenseResponse.model_validate(expense)


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    request: ExpenseUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Update an existing expense."""
    if request.name is None and request.category is None and request.amount is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided.",
        )
    expense = expense_service.update_expense(
        user_id=current_user.id,
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
def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Delete and return an expense by ID."""
    expense = expense_service.delete_expense(current_user.id, expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} was not found.",
        )
    return ExpenseResponse.model_validate(expense)
