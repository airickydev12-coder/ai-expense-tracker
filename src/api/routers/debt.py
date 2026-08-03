"""Debt API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user
from src.api.schemas.debt import (
    DebtCreateRequest,
    DebtPaymentRequest,
    DebtResponse,
    DebtUpdateRequest,
)
from src.financial.debt import service as debt_service
from src.financial.debt.models import Debt
from src.financial.users.models import User

router = APIRouter(prefix="/debts", tags=["Debt"])


@router.get("", response_model=list[DebtResponse])
def list_debts(current_user: User = Depends(get_current_user)) -> list[Debt]:
    """Return all recorded debts."""
    return debt_service.get_debts(current_user.id)


@router.get("/{debt_id}", response_model=DebtResponse)
def get_debt(
    debt_id: int,
    current_user: User = Depends(get_current_user),
) -> DebtResponse:
    """Return a debt by ID."""
    debt = debt_service.get_debt_by_id(current_user.id, debt_id)
    if debt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debt with ID {debt_id} was not found.",
        )
    return DebtResponse.model_validate(debt)


@router.post("", response_model=DebtResponse, status_code=status.HTTP_201_CREATED)
def create_debt(
    request: DebtCreateRequest,
    current_user: User = Depends(get_current_user),
) -> DebtResponse:
    """Create a new debt."""
    debt = debt_service.add_debt(
        user_id=current_user.id,
        name=request.name,
        balance=request.balance,
        interest_rate=request.interest_rate,
        minimum_payment=request.minimum_payment,
    )
    return DebtResponse.model_validate(debt)


@router.put("/{debt_id}", response_model=DebtResponse)
def update_debt(
    debt_id: int,
    request: DebtUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> DebtResponse:
    """Update an existing debt."""
    if (
        request.name is None
        and request.balance is None
        and request.interest_rate is None
        and request.minimum_payment is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided.",
        )
    debt = debt_service.update_debt(
        user_id=current_user.id,
        debt_id=debt_id,
        name=request.name,
        balance=request.balance,
        interest_rate=request.interest_rate,
        minimum_payment=request.minimum_payment,
    )
    if debt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debt with ID {debt_id} was not found.",
        )
    return DebtResponse.model_validate(debt)


@router.post("/{debt_id}/payments", response_model=DebtResponse)
def apply_payment(
    debt_id: int,
    request: DebtPaymentRequest,
    current_user: User = Depends(get_current_user),
) -> DebtResponse:
    """Apply a payment to a debt."""
    debt = debt_service.apply_payment_to_debt(
        user_id=current_user.id,
        debt_id=debt_id,
        payment=request.payment,
    )
    if debt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debt with ID {debt_id} was not found.",
        )
    return DebtResponse.model_validate(debt)


@router.delete("/{debt_id}", response_model=DebtResponse)
def delete_debt(
    debt_id: int,
    current_user: User = Depends(get_current_user),
) -> DebtResponse:
    """Delete and return a debt by ID."""
    debt = debt_service.delete_debt(current_user.id, debt_id)
    if debt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debt with ID {debt_id} was not found.",
        )
    return DebtResponse.model_validate(debt)
