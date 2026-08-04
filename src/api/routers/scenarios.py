"""Financial scenario API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user
from src.api.schemas.scenarios import (
    ScenarioCombinedRequest,
    ScenarioOptimizeRequest,
    ScenarioParseRequest,
    ScenarioRunRequest,
)
from src.financial.application.financial_state import (
    build_current_financial_snapshot,
)
from src.financial.debt.service import get_debts
from src.financial.scenarios import nl_builder
from src.financial.scenarios.combined import run_combined_scenario_plan
from src.financial.scenarios.models import ScenarioRequest
from src.financial.scenarios.optimizer import optimize_financial_snapshot
from src.financial.scenarios.service import run_financial_scenario
from src.financial.scenarios.workspace_service import (
    clear_persisted_scenario_workspace,
    get_scenario_workspace,
    remove_result_from_workspace,
    save_result_to_workspace,
)
from src.financial.shared.categories import ExpenseCategory
from src.financial.users.models import User

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


def _build_request(request: ScenarioRunRequest) -> ScenarioRequest:
    return ScenarioRequest(
        scenario_type=request.scenario_type,
        name=request.name,
        description=request.description,
        parameters=request.parameters,
    )


@router.post("/run")
def run_scenario(
    request: ScenarioRunRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Run one financial scenario against the current financial state."""
    snapshot = build_current_financial_snapshot(current_user.id)
    result = run_financial_scenario(_build_request(request), snapshot)
    return result.to_dict()


@router.post("/parse")
def parse_scenario(
    request: ScenarioParseRequest,
    current_user: User = Depends(get_current_user),
) -> ScenarioRunRequest:
    """Parse free text into a scenario draft to prefill the Run form."""
    categories = [category.value for category in ExpenseCategory]
    debts = get_debts(current_user.id)
    draft = nl_builder.parse_scenario_text(request.text, categories, debts)
    return ScenarioRunRequest(**draft)


@router.post("/optimize")
def optimize_scenarios(
    request: ScenarioOptimizeRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Run the scenario optimizer against the current financial state."""
    snapshot = build_current_financial_snapshot(current_user.id)
    result = optimize_financial_snapshot(
        snapshot,
        limit=request.limit,
        ranking_metric=request.ranking_metric,
        horizon_months=request.horizon_months,
        register_handlers=False,
    )
    return result.to_dict()


@router.post("/combined")
def run_combined_plan(
    request: ScenarioCombinedRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Run a combined, multi-step scenario plan."""
    snapshot = build_current_financial_snapshot(current_user.id)
    result = run_combined_scenario_plan(
        name=request.name,
        description=request.description,
        requests=[_build_request(item) for item in request.requests],
        snapshot=snapshot,
    )
    return result.to_dict()


@router.get("/workspace")
def list_workspace_results(
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Return all scenario results saved to the workspace."""
    return [
        result.to_dict() for result in get_scenario_workspace(current_user.id).get_results()
    ]


@router.post("/workspace", status_code=status.HTTP_201_CREATED)
def save_workspace_result(
    request: ScenarioRunRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Run a scenario and save the result to the workspace."""
    snapshot = build_current_financial_snapshot(current_user.id)
    result = run_financial_scenario(_build_request(request), snapshot)
    save_result_to_workspace(current_user.id, result)
    return result.to_dict()


@router.delete("/workspace/{scenario_name}")
def delete_workspace_result(
    scenario_name: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Remove one scenario result from the workspace."""
    removed = remove_result_from_workspace(current_user.id, scenario_name)
    if removed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No workspace scenario named '{scenario_name}' was found.",
        )
    return removed.to_dict()


@router.delete("/workspace", status_code=status.HTTP_204_NO_CONTENT)
def clear_workspace(current_user: User = Depends(get_current_user)) -> None:
    """Clear every scenario result saved to the workspace."""
    clear_persisted_scenario_workspace(current_user.id)
