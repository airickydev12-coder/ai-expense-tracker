"""Goal and goal-ledger API endpoints."""

from fastapi import APIRouter, HTTPException, status

from src.api.schemas.goals import (
    GoalCreateRequest,
    GoalLedgerEntryResponse,
    GoalLedgerOperationRequest,
    GoalReconcileResponse,
    GoalResponse,
    GoalReversalRequest,
    GoalUpdateRequest,
)
from src.financial.goal_ledger.models import GoalLedgerEntry
from src.financial.goals import service as goal_service
from src.financial.goals.models import Goal

router = APIRouter(prefix="/goals", tags=["Goals"])


def _not_found(goal_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Goal with ID {goal_id} was not found.",
    )


@router.get("", response_model=list[GoalResponse])
def list_goals() -> list[Goal]:
    """Return all recorded goals."""
    return goal_service.get_goals()


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(goal_id: int) -> GoalResponse:
    """Return a goal by ID."""
    goal = goal_service.get_goal_by_id(goal_id)
    if goal is None:
        raise _not_found(goal_id)
    return GoalResponse.model_validate(goal)


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(request: GoalCreateRequest) -> GoalResponse:
    """Create a new goal."""
    goal = goal_service.add_goal(
        name=request.name,
        target_amount=request.target_amount,
        current_amount=request.current_amount,
    )
    return GoalResponse.model_validate(goal)


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    request: GoalUpdateRequest,
) -> GoalResponse:
    """Update an existing goal."""
    if (
        request.name is None
        and request.target_amount is None
        and request.current_amount is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided.",
        )
    goal = goal_service.update_goal(
        goal_id=goal_id,
        name=request.name,
        target_amount=request.target_amount,
        current_amount=request.current_amount,
    )
    if goal is None:
        raise _not_found(goal_id)
    return GoalResponse.model_validate(goal)


@router.get("/{goal_id}/ledger", response_model=list[GoalLedgerEntryResponse])
def get_goal_ledger(goal_id: int) -> list[GoalLedgerEntry]:
    """Return all ledger entries recorded for a goal."""
    if goal_service.get_goal_by_id(goal_id) is None:
        raise _not_found(goal_id)
    return goal_service.get_goal_ledger_entries(goal_id)


@router.get("/{goal_id}/reconcile", response_model=GoalReconcileResponse)
def reconcile_goal(goal_id: int) -> GoalReconcileResponse:
    """Compare a goal's cached balance against its ledger-derived balance."""
    result = goal_service.reconcile_goal(goal_id)
    if result is None:
        raise _not_found(goal_id)
    is_reconciled, ledger_balance = result
    return GoalReconcileResponse(
        is_reconciled=is_reconciled,
        ledger_balance=float(ledger_balance),
    )


@router.post("/{goal_id}/contributions", response_model=GoalResponse)
def contribute_to_goal(
    goal_id: int,
    request: GoalLedgerOperationRequest,
) -> GoalResponse:
    """Record a contribution to a goal."""
    goal = goal_service.contribute_to_goal(
        goal_id=goal_id,
        contribution=request.amount,
        effective_date=request.effective_date,
        source=request.source,
        note=request.note,
        correlation_id=request.correlation_id,
    )
    if goal is None:
        raise _not_found(goal_id)
    return GoalResponse.model_validate(goal)


@router.post("/{goal_id}/withdrawals", response_model=GoalResponse)
def withdraw_from_goal(
    goal_id: int,
    request: GoalLedgerOperationRequest,
) -> GoalResponse:
    """Record a withdrawal from a goal."""
    goal = goal_service.withdraw_from_goal(
        goal_id=goal_id,
        amount=request.amount,
        effective_date=request.effective_date,
        source=request.source,
        note=request.note,
        correlation_id=request.correlation_id,
    )
    if goal is None:
        raise _not_found(goal_id)
    return GoalResponse.model_validate(goal)


@router.post("/{goal_id}/adjustments", response_model=GoalResponse)
def adjust_goal_balance(
    goal_id: int,
    request: GoalLedgerOperationRequest,
) -> GoalResponse:
    """Record a signed balance correction for a goal."""
    goal = goal_service.adjust_goal_balance(
        goal_id=goal_id,
        amount=request.amount,
        effective_date=request.effective_date,
        source=request.source,
        note=request.note,
        correlation_id=request.correlation_id,
    )
    if goal is None:
        raise _not_found(goal_id)
    return GoalResponse.model_validate(goal)


@router.post("/{goal_id}/reversals", response_model=GoalResponse)
def reverse_goal_ledger_entry(
    goal_id: int,
    request: GoalReversalRequest,
) -> GoalResponse:
    """Reverse a ledger entry belonging to a goal."""
    goal = goal_service.reverse_goal_ledger_entry(
        goal_id=goal_id,
        entry_id=request.entry_id,
        effective_date=request.effective_date,
        source=request.source,
        note=request.note,
        correlation_id=request.correlation_id,
    )
    if goal is None:
        raise _not_found(goal_id)
    return GoalResponse.model_validate(goal)


@router.delete("/{goal_id}", response_model=GoalResponse)
def delete_goal(goal_id: int) -> GoalResponse:
    """Delete and return a goal by ID."""
    goal = goal_service.delete_goal(goal_id)
    if goal is None:
        raise _not_found(goal_id)
    return GoalResponse.model_validate(goal)
