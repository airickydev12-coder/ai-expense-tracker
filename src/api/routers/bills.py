"""Bill API endpoints."""

from fastapi import APIRouter, HTTPException, status

from src.api.schemas.bills import (
    BillCreateRequest,
    BillResponse,
    BillUpdateRequest,
)
from src.financial.bills import service as bill_service
from src.financial.bills.models import Bill

router = APIRouter(prefix="/bills", tags=["Bills"])


@router.get("", response_model=list[BillResponse])
def list_bills() -> list[Bill]:
    """Return all recorded bills."""
    return bill_service.get_bills()


@router.get("/{bill_id}", response_model=BillResponse)
def get_bill(bill_id: int) -> BillResponse:
    """Return a bill by ID."""
    bill = bill_service.get_bill_by_id(bill_id)
    if bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with ID {bill_id} was not found.",
        )
    return BillResponse.model_validate(bill)


@router.post("", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
def create_bill(request: BillCreateRequest) -> BillResponse:
    """Create a new bill."""
    bill = bill_service.add_bill(
        name=request.name,
        amount=request.amount,
        due_day=request.due_day,
        is_paid=request.is_paid,
    )
    return BillResponse.model_validate(bill)


@router.put("/{bill_id}", response_model=BillResponse)
def update_bill(
    bill_id: int,
    request: BillUpdateRequest,
) -> BillResponse:
    """Update an existing bill."""
    if (
        request.name is None
        and request.amount is None
        and request.due_day is None
        and request.is_paid is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided.",
        )
    bill = bill_service.update_bill(
        bill_id=bill_id,
        name=request.name,
        amount=request.amount,
        due_day=request.due_day,
        is_paid=request.is_paid,
    )
    if bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with ID {bill_id} was not found.",
        )
    return BillResponse.model_validate(bill)


@router.patch("/{bill_id}/pay", response_model=BillResponse)
def pay_bill(bill_id: int) -> BillResponse:
    """Mark a bill as paid."""
    bill = bill_service.mark_bill_paid(bill_id)
    if bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with ID {bill_id} was not found.",
        )
    return BillResponse.model_validate(bill)


@router.patch("/{bill_id}/unpay", response_model=BillResponse)
def unpay_bill(bill_id: int) -> BillResponse:
    """Mark a bill as unpaid."""
    bill = bill_service.mark_bill_unpaid(bill_id)
    if bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with ID {bill_id} was not found.",
        )
    return BillResponse.model_validate(bill)


@router.delete("/{bill_id}", response_model=BillResponse)
def delete_bill(bill_id: int) -> BillResponse:
    """Delete and return a bill by ID."""
    bill = bill_service.delete_bill(bill_id)
    if bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with ID {bill_id} was not found.",
        )
    return BillResponse.model_validate(bill)
