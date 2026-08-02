"""Financial scenario API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

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
from src.financial.scenarios.workspace import get_saved_scenario_results
from src.financial.scenarios.workspace_service import (
    clear_persisted_scenario_workspace,
    remove_result_from_workspace,
    save_result_to_workspace,
)
from src.financial.shared.categories import ExpenseCategory

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


def _build_request(request: ScenarioRunRequest) -> ScenarioRequest:
    return ScenarioRequest(
        scenario_type=request.scenario_type,
        name=request.name,
        description=request.description,
        parameters=request.parameters,
    )


@router.post("/run")
def run_scenario(request: ScenarioRunRequest) -> dict[str, Any]:
    """Run one financial scenario against the current financial state."""
    snapshot = build_current_financial_snapshot()
    result = run_financial_scenario(_build_request(request), snapshot)
    return result.to_dict()


@router.post("/parse")
def parse_scenario(request: ScenarioParseRequest) -> ScenarioRunRequest:
    """Parse free text into a scenario draft to prefill the Run form."""
    categories = [category.value for category in ExpenseCategory]
    debts = get_debts()
    draft = nl_builder.parse_scenario_text(request.text, categories, debts)
    return ScenarioRunRequest(**draft)


@router.post("/optimize")
def optimize_scenarios(request: ScenarioOptimizeRequest) -> dict[str, Any]:
    """Run the scenario optimizer against the current financial state."""
    snapshot = build_current_financial_snapshot()
    result = optimize_financial_snapshot(
        snapshot,
        limit=request.limit,
        ranking_metric=request.ranking_metric,
        horizon_months=request.horizon_months,
        register_handlers=False,
    )
    return result.to_dict()


@router.post("/combined")
def run_combined_plan(request: ScenarioCombinedRequest) -> dict[str, Any]:
    """Run a combined, multi-step scenario plan."""
    snapshot = build_current_financial_snapshot()
    result = run_combined_scenario_plan(
        name=request.name,
        description=request.description,
        requests=[_build_request(item) for item in request.requests],
        snapshot=snapshot,
    )
    return result.to_dict()


@router.get("/workspace")
def list_workspace_results() -> list[dict[str, Any]]:
    """Return all scenario results saved to the workspace."""
    return [result.to_dict() for result in get_saved_scenario_results()]


@router.post("/workspace", status_code=status.HTTP_201_CREATED)
def save_workspace_result(request: ScenarioRunRequest) -> dict[str, Any]:
    """Run a scenario and save the result to the workspace."""
    snapshot = build_current_financial_snapshot()
    result = run_financial_scenario(_build_request(request), snapshot)
    save_result_to_workspace(result)
    return result.to_dict()


@router.delete("/workspace/{scenario_name}")
def delete_workspace_result(scenario_name: str) -> dict[str, Any]:
    """Remove one scenario result from the workspace."""
    removed = remove_result_from_workspace(scenario_name)
    if removed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No workspace scenario named '{scenario_name}' was found.",
        )
    return removed.to_dict()


@router.delete("/workspace", status_code=status.HTTP_204_NO_CONTENT)
def clear_workspace() -> None:
    """Clear every scenario result saved to the workspace."""
    clear_persisted_scenario_workspace()
