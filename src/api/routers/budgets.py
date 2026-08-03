"""API endpoints for budget management."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user
from src.api.schemas.budgets import (
    BudgetCreateRequest,
    BudgetResponse,
    BudgetUpdateRequest,
)
from src.financial.budgets import service as budget_service
from src.financial.shared.categories import ExpenseCategory
from src.financial.users.models import User

router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"],
)


@router.get(
    "",
    response_model=list[BudgetResponse],
)
def get_budgets(current_user: User = Depends(get_current_user)) -> list[BudgetResponse]:
    """Return all budgets."""
    return [
        BudgetResponse.model_validate(budget)
        for budget in budget_service.get_budgets(current_user.id)
    ]


@router.get(
    "/{category}",
    response_model=BudgetResponse,
)
def get_budget(
    category: ExpenseCategory,
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    """Return a budget by category."""
    budget = budget_service.get_budget_by_category(current_user.id, category)

    if budget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget for category '{category.value}' was not found.",
        )

    return BudgetResponse.model_validate(budget)


@router.post(
    "",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_budget(
    request: BudgetCreateRequest,
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    """Create a new budget or replace an existing one."""
    budget = budget_service.add_budget(
        user_id=current_user.id,
        category=request.category,
        limit=request.limit,
    )

    return BudgetResponse.model_validate(budget)


@router.put(
    "/{category}",
    response_model=BudgetResponse,
)
def update_budget(
    category: ExpenseCategory,
    request: BudgetUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    """Update an existing budget."""
    existing_budget = budget_service.get_budget_by_category(current_user.id, category)

    if existing_budget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget for category '{category.value}' was not found.",
        )

    budget = budget_service.update_budget(
        user_id=current_user.id,
        category=category,
        limit=request.limit,
    )

    return BudgetResponse.model_validate(budget)


@router.delete(
    "/{category}",
    response_model=BudgetResponse,
)
def delete_budget(
    category: ExpenseCategory,
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    """Delete a budget."""
    deleted_budget = budget_service.delete_budget(current_user.id, category)

    if deleted_budget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget for category '{category.value}' was not found.",
        )

    return BudgetResponse.model_validate(deleted_budget)
