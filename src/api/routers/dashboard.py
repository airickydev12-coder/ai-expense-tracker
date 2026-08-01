"""API routes for the financial dashboard."""

from fastapi import APIRouter

from src.api.schemas.dashboard import DashboardResponse
from src.financial.application.dashboard_service import build_dashboard

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard() -> DashboardResponse:
    """Return the aggregated financial dashboard."""

    dashboard = build_dashboard()

    return DashboardResponse.model_validate(dashboard)
