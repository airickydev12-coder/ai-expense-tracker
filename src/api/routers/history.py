"""Financial history API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from src.api.schemas.history import FinancialSnapshotResponse
from src.financial.application.financial_state import (
    record_current_financial_snapshot,
)
from src.financial.history import service as history_service
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.trends import analyze_financial_trends

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", response_model=list[FinancialSnapshotResponse])
def list_history() -> list[FinancialSnapshotRecord]:
    """Return all recorded financial snapshots."""
    return history_service.get_history()


@router.get("/latest", response_model=FinancialSnapshotResponse)
def get_latest_snapshot() -> FinancialSnapshotResponse:
    """Return the most recent financial snapshot."""
    snapshot = history_service.get_latest_snapshot()
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No financial snapshots have been recorded.",
        )
    return FinancialSnapshotResponse.model_validate(snapshot)


@router.get("/trends")
def get_trends() -> dict[str, Any]:
    """Return a trend analysis across all recorded snapshots."""
    trends = analyze_financial_trends(history_service.get_history())
    return trends.to_dict()


@router.post(
    "/snapshot",
    response_model=FinancialSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_snapshot() -> FinancialSnapshotResponse:
    """Build and record a snapshot from the current financial state."""
    _, record = record_current_financial_snapshot()
    return FinancialSnapshotResponse.model_validate(record)
