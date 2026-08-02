"""API schemas for goal and goal-ledger endpoints."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GoalCreateRequest(BaseModel):
    """Request body for creating a goal."""

    name: str = Field(min_length=1)
    target_amount: Decimal = Field(gt=0)
    current_amount: Decimal = Field(default=Decimal("0"), ge=0)


class GoalUpdateRequest(BaseModel):
    """Request body for updating a goal."""

    name: str | None = Field(default=None, min_length=1)
    target_amount: Decimal | None = Field(default=None, gt=0)
    current_amount: Decimal | None = Field(default=None, ge=0)


class GoalResponse(BaseModel):
    """Serialized representation of a goal."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    target_amount: float
    current_amount: float


class GoalLedgerOperationRequest(BaseModel):
    """Request body shared by contribution/withdrawal/adjustment operations."""

    amount: Decimal
    effective_date: date | None = None
    source: str = "MANUAL"
    note: str = ""
    correlation_id: str | None = None


class GoalReversalRequest(BaseModel):
    """Request body for reversing a ledger entry."""

    entry_id: str
    effective_date: date | None = None
    source: str = "MANUAL"
    note: str = ""
    correlation_id: str | None = None


class GoalLedgerEntryResponse(BaseModel):
    """Serialized representation of one goal-ledger entry."""

    model_config = ConfigDict(from_attributes=True)

    entry_id: str
    goal_id: int
    entry_type: str
    amount: float
    effective_date: date
    created_at: datetime
    source: str
    note: str
    correlation_id: str | None
    reverses_entry_id: str | None


class GoalReconcileResponse(BaseModel):
    """Result of comparing a goal's cached balance to its ledger."""

    is_reconciled: bool
    ledger_balance: float
