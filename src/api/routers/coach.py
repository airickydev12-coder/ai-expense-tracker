"""AI financial coach API endpoints."""

from typing import Any

from fastapi import APIRouter

from src.financial.application.financial_state import (
    build_current_financial_snapshot,
)
from src.financial.coach.coaching import build_coaching_session
from src.financial.coach.insights import generate_financial_coach_insights
from src.financial.scenarios.optimizer import optimize_financial_snapshot

router = APIRouter(prefix="/coach", tags=["Coach"])


@router.get("/insights")
def get_insights() -> list[dict[str, Any]]:
    """Return deterministic coaching insights for the current financial state."""
    snapshot = build_current_financial_snapshot()
    insights = generate_financial_coach_insights(snapshot)
    return [insight.to_dict() for insight in insights]


@router.get("/session")
def get_coaching_session() -> dict[str, Any]:
    """Build a complete coaching session from the current financial state."""
    snapshot = build_current_financial_snapshot()
    optimization_result = optimize_financial_snapshot(
        snapshot,
        register_handlers=False,
    )
    session = build_coaching_session(snapshot, optimization_result)
    return session.to_dict()
