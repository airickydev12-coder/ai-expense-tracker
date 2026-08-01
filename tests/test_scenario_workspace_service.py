from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.workspace import (
    scenario_workspace,
)
from src.financial.scenarios.workspace_repository import (
    load_workspace_from_file,
)
from src.financial.scenarios.workspace_service import (
    clear_persisted_scenario_workspace,
    get_scenario_workspace,
    load_scenario_workspace,
    remove_result_from_workspace,
    save_result_to_workspace,
    save_scenario_workspace,
)


def build_snapshot() -> dict:
    """Create a reusable scenario snapshot."""
    return {
        "total_income": 5000,
        "total_expenses": 3000,
        "net_cash_flow": 2000,
        "total_account_balance": 8000,
        "total_goal_progress": 2500,
        "total_debt": 10000,
        "net_worth": 500,
        "health_score": 70,
        "health_status": "Good",
    }


def build_result(
    name: str = "Income Increase",
    net_worth: float = 6500,
) -> ScenarioResult:
    """Create a reusable scenario result."""
    original_snapshot = build_snapshot()

    return ScenarioResult(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name=name,
        description="",
        assumptions=[],
        original_snapshot=original_snapshot,
        projected_snapshot={
            **original_snapshot,
            "net_worth": net_worth,
        },
        impacts=[],
    )


def setup_function():
    """Clear the shared workspace before each test."""
    scenario_workspace.clear()


def teardown_function():
    """Clear the shared workspace after each test."""
    scenario_workspace.clear()


def test_save_result_to_workspace(
    tmp_path,
):
    file_path = tmp_path / "scenario_workspace.json"

    result = build_result()

    save_result_to_workspace(
        result,
        file_path,
    )

    assert scenario_workspace.count() == 1
    assert file_path.exists()


def test_saved_result_is_restored_after_reload(
    tmp_path,
):
    file_path = tmp_path / "scenario_workspace.json"

    save_result_to_workspace(
        build_result(),
        file_path,
    )

    scenario_workspace.clear()

    assert scenario_workspace.is_empty()

    load_scenario_workspace(file_path)

    assert scenario_workspace.count() == 1
    assert scenario_workspace.get_result("Income Increase") is not None


def test_duplicate_result_name_is_replaced(
    tmp_path,
):
    file_path = tmp_path / "scenario_workspace.json"

    save_result_to_workspace(
        build_result(
            name="Income Increase",
            net_worth=6500,
        ),
        file_path,
    )

    save_result_to_workspace(
        build_result(
            name="income increase",
            net_worth=9000,
        ),
        file_path,
    )

    assert scenario_workspace.count() == 1

    result = scenario_workspace.get_results()[0]

    assert result.projected_snapshot["net_worth"] == 9000


def test_remove_result_from_workspace(
    tmp_path,
):
    file_path = tmp_path / "scenario_workspace.json"

    save_result_to_workspace(
        build_result(),
        file_path,
    )

    removed = remove_result_from_workspace(
        "income increase",
        file_path,
    )

    assert removed is not None
    assert scenario_workspace.is_empty()

    load_scenario_workspace(file_path)

    assert scenario_workspace.is_empty()


def test_remove_missing_result_returns_none(
    tmp_path,
):
    file_path = tmp_path / "scenario_workspace.json"

    removed = remove_result_from_workspace(
        "Missing",
        file_path,
    )

    assert removed is None


def test_save_scenario_workspace(
    tmp_path,
):
    file_path = tmp_path / "scenario_workspace.json"

    scenario_workspace.add_result(build_result())

    save_scenario_workspace(file_path)

    assert file_path.exists()


def test_clear_persisted_workspace(
    tmp_path,
):
    file_path = tmp_path / "scenario_workspace.db"

    save_result_to_workspace(
        build_result(),
        file_path,
    )

    clear_persisted_scenario_workspace(file_path)

    assert scenario_workspace.is_empty()
    assert load_workspace_from_file(file_path) == []


def test_get_scenario_workspace():
    assert get_scenario_workspace() is scenario_workspace
