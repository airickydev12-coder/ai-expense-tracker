"""Income API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user
from src.api.schemas.income import (
    IncomeCreateRequest,
    IncomeResponse,
    IncomeUpdateRequest,
)
from src.financial.income import service as income_service
from src.financial.income.models import Income
from src.financial.users.models import User

router = APIRouter(prefix="/income", tags=["Income"])


@router.get("", response_model=list[IncomeResponse])
def list_income(current_user: User = Depends(get_current_user)) -> list[Income]:
    """Return all recorded income entries."""
    return income_service.get_income_entries(current_user.id)


@router.get("/{income_id}", response_model=IncomeResponse)
def get_income(
    income_id: int,
    current_user: User = Depends(get_current_user),
) -> IncomeResponse:
    """Return an income entry by ID."""
    income = income_service.get_income_by_id(current_user.id, income_id)
    if income is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Income entry with ID {income_id} was not found.",
        )
    return IncomeResponse.model_validate(income)


@router.post("", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
def create_income(
    request: IncomeCreateRequest,
    current_user: User = Depends(get_current_user),
) -> IncomeResponse:
    """Create a new income entry."""
    income = income_service.add_income(
        user_id=current_user.id,
        source=request.source,
        amount=request.amount,
    )
    return IncomeResponse.model_validate(income)


@router.put("/{income_id}", response_model=IncomeResponse)
def update_income(
    income_id: int,
    request: IncomeUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> IncomeResponse:
    """Update an existing income entry."""
    if request.source is None and request.amount is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided.",
        )
    income = income_service.update_income(
        user_id=current_user.id,
        income_id=income_id,
        source=request.source,
        amount=request.amount,
    )
    if income is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Income entry with ID {income_id} was not found.",
        )
    return IncomeResponse.model_validate(income)


@router.delete("/{income_id}", response_model=IncomeResponse)
def delete_income(
    income_id: int,
    current_user: User = Depends(get_current_user),
) -> IncomeResponse:
    """Delete and return an income entry by ID."""
    income = income_service.delete_income(current_user.id, income_id)
    if income is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Income entry with ID {income_id} was not found.",
        )
    return IncomeResponse.model_validate(income)
