"""Account API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user
from src.api.schemas.accounts import (
    AccountCreateRequest,
    AccountResponse,
    AccountUpdateRequest,
)
from src.financial.accounts import service as account_service
from src.financial.accounts.models import Account
from src.financial.users.models import User

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("", response_model=list[AccountResponse])
def list_accounts(current_user: User = Depends(get_current_user)) -> list[Account]:
    """Return all recorded accounts."""
    return account_service.get_accounts(current_user.id)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
) -> AccountResponse:
    """Return an account by ID."""
    account = account_service.get_account_by_id(current_user.id, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} was not found.",
        )
    return AccountResponse.model_validate(account)


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    request: AccountCreateRequest,
    current_user: User = Depends(get_current_user),
) -> AccountResponse:
    """Create a new account."""
    account = account_service.add_account(
        user_id=current_user.id,
        name=request.name,
        account_type=request.account_type,
        balance=request.balance,
    )
    return AccountResponse.model_validate(account)


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    request: AccountUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> AccountResponse:
    """Update an existing account."""
    if (
        request.name is None
        and request.account_type is None
        and request.balance is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided.",
        )
    account = account_service.update_account(
        user_id=current_user.id,
        account_id=account_id,
        name=request.name,
        account_type=request.account_type,
        balance=request.balance,
    )
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} was not found.",
        )
    return AccountResponse.model_validate(account)


@router.delete("/{account_id}", response_model=AccountResponse)
def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
) -> AccountResponse:
    """Delete and return an account by ID."""
    account = account_service.delete_account(current_user.id, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} was not found.",
        )
    return AccountResponse.model_validate(account)
