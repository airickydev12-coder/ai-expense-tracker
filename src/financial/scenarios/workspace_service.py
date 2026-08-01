from pathlib import Path

from src.core.config import DB_PATH
from src.financial.scenarios.models import (
    ScenarioResult,
)
from src.financial.scenarios.workspace import (
    ScenarioWorkspace,
    scenario_workspace,
)
from src.financial.scenarios.workspace_repository import (
    clear_workspace_file,
    load_workspace_from_file,
    save_workspace_to_file,
)

_loaded_workspace_file: Path = DB_PATH


def load_scenario_workspace(
    file_path: Path = DB_PATH,
) -> None:
    """Load the persisted scenario workspace into memory."""
    global _loaded_workspace_file

    results = load_workspace_from_file(file_path)

    scenario_workspace.clear()

    for result in results:
        scenario_workspace.add_result(result)

    _loaded_workspace_file = file_path


def save_scenario_workspace(
    file_path: Path | None = None,
) -> None:
    """Persist the current scenario workspace."""
    target_path = file_path if file_path is not None else _loaded_workspace_file

    save_workspace_to_file(
        scenario_workspace.get_results(),
        target_path,
    )


def save_result_to_workspace(
    result: ScenarioResult,
    file_path: Path | None = None,
) -> None:
    """Add or replace a result and persist the workspace."""
    scenario_workspace.add_result(result)

    save_scenario_workspace(file_path)


def remove_result_from_workspace(
    scenario_name: str,
    file_path: Path | None = None,
) -> ScenarioResult | None:
    """Remove one scenario result and persist the change."""
    removed = scenario_workspace.remove_result(scenario_name)

    if removed is None:
        return None

    save_scenario_workspace(file_path)

    return removed


def clear_persisted_scenario_workspace(
    file_path: Path | None = None,
) -> None:
    """Clear both in-memory and persisted workspace data."""
    target_path = file_path if file_path is not None else _loaded_workspace_file

    scenario_workspace.clear()
    clear_workspace_file(target_path)


def get_scenario_workspace() -> ScenarioWorkspace:
    """Return the shared scenario workspace."""
    return scenario_workspace
