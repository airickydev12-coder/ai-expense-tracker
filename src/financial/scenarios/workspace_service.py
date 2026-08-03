from pathlib import Path

from src.core.config import DB_PATH
from src.financial.scenarios.models import (
    ScenarioResult,
)
from src.financial.scenarios.workspace import (
    ScenarioWorkspace,
)
from src.financial.scenarios.workspace_repository import (
    clear_workspace_file,
    load_workspace_from_file,
    save_workspace_to_file,
)

_workspaces: dict[int, ScenarioWorkspace] = {}
_loaded_workspace_files: dict[int, Path] = {}


def _ensure_loaded(user_id: int, file_path: Path = DB_PATH) -> None:
    """Lazily load a user's scenario workspace into the cache on first access."""
    if user_id not in _workspaces:
        load_scenario_workspace(user_id, file_path)


def load_scenario_workspace(
    user_id: int,
    file_path: Path = DB_PATH,
) -> None:
    """Load a user's persisted scenario workspace into memory."""
    results = load_workspace_from_file(user_id, file_path)

    workspace = ScenarioWorkspace()
    for result in results:
        workspace.add_result(result)

    _workspaces[user_id] = workspace
    _loaded_workspace_files[user_id] = file_path


def save_scenario_workspace(user_id: int, file_path: Path | None = None) -> None:
    """Persist a user's current scenario workspace."""
    target_path = file_path if file_path is not None else _loaded_workspace_files.get(user_id)

    if target_path is None:
        target_path = DB_PATH

    save_workspace_to_file(
        _workspaces[user_id].get_results(),
        user_id,
        target_path,
    )


def save_result_to_workspace(
    user_id: int,
    result: ScenarioResult,
    file_path: Path | None = None,
) -> None:
    """Add or replace a result and persist this user's workspace."""
    _ensure_loaded(user_id, file_path if file_path is not None else DB_PATH)

    _workspaces[user_id].add_result(result)

    save_scenario_workspace(user_id, file_path)


def remove_result_from_workspace(
    user_id: int,
    scenario_name: str,
    file_path: Path | None = None,
) -> ScenarioResult | None:
    """Remove one of a user's scenario results and persist the change."""
    _ensure_loaded(user_id, file_path if file_path is not None else DB_PATH)

    removed = _workspaces[user_id].remove_result(scenario_name)

    if removed is None:
        return None

    save_scenario_workspace(user_id, file_path)

    return removed


def clear_persisted_scenario_workspace(user_id: int, file_path: Path | None = None) -> None:
    """Clear both in-memory and persisted workspace data for this user."""
    target_path = file_path if file_path is not None else _loaded_workspace_files.get(user_id)

    if target_path is None:
        target_path = DB_PATH

    _workspaces[user_id] = ScenarioWorkspace()
    clear_workspace_file(user_id, target_path)


def get_scenario_workspace(user_id: int, file_path: Path = DB_PATH) -> ScenarioWorkspace:
    """Return this user's scenario workspace."""
    _ensure_loaded(user_id, file_path)
    return _workspaces[user_id]
