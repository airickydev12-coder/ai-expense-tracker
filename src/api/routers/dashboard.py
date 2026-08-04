"""API routes for the financial dashboard."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user
from src.api.schemas.dashboard import DashboardResponse
from src.financial.application.dashboard_service import build_dashboard
from src.financial.users.models import User

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard(current_user: User = Depends(get_current_user)) -> DashboardResponse:
    """Return the aggregated financial dashboard."""

    dashboard = build_dashboard(current_user.id)

    return DashboardResponse.model_validate(dashboard)
