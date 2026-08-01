"""Account API endpoints."""

from fastapi import APIRouter, HTTPException, status

from src.api.schemas.accounts import (
    AccountCreateRequest,
    AccountResponse,
    AccountUpdateRequest,
)
from src.financial.accounts import service as account_service
from src.financial.accounts.models import Account

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("", response_model=list[AccountResponse])
def list_accounts() -> list[Account]:
    """Return all recorded accounts."""
    return account_service.get_accounts()


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int) -> AccountResponse:
    """Return an account by ID."""
    account = account_service.get_account_by_id(account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} was not found.",
        )
    return AccountResponse.model_validate(account)


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(request: AccountCreateRequest) -> AccountResponse:
    """Create a new account."""
    account = account_service.add_account(
        name=request.name,
        account_type=request.account_type,
        balance=request.balance,
    )
    return AccountResponse.model_validate(account)


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    request: AccountUpdateRequest,
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
def delete_account(account_id: int) -> AccountResponse:
    """Delete and return an account by ID."""
    account = account_service.delete_account(account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} was not found.",
        )
    return AccountResponse.model_validate(account)
