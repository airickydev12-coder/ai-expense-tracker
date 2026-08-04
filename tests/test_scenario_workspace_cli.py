import pytest

from src.core.db import clear_test_database, initialize_database, set_test_database
from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
)
from src.financial.scenarios import workspace_service
from src.financial.scenarios.workspace_service import save_result_to_workspace
from src.presentation import scenario_workspace_cli

TEST_USER_ID = 1


def build_result(
    name: str,
    net_worth: float,
) -> ScenarioResult:
    """Create a workspace CLI result."""
    original = {
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

    return ScenarioResult(
        scenario_type=ScenarioType.INCOME_INCREASE,
        name=name,
        description="",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot={
            **original,
            "net_worth": net_worth,
        },
        impacts=[],
    )


@pytest.fixture(autouse=True)
def _isolated_database(monkeypatch, tmp_path):
    """Redirect the default DB_PATH to a throwaway database for this file."""
    test_db_path = tmp_path / "test_app.db"
    initialize_database(test_db_path)
    set_test_database(test_db_path)

    workspace_service._workspaces.clear()
    workspace_service._loaded_workspace_files.clear()

    monkeypatch.setattr(scenario_workspace_cli, "get_cli_user_id", lambda: TEST_USER_ID)

    yield

    clear_test_database()


def test_select_ranking_metric(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "2",
    )

    result = scenario_workspace_cli.select_ranking_metric()

    assert result == (ScenarioRankingMetric.NET_WORTH)


def test_display_saved_scenarios(
    capsys,
):
    save_result_to_workspace(
        TEST_USER_ID,
        build_result(
            "Income Increase",
            6500,
        ),
    )

    scenario_workspace_cli.display_saved_scenarios()

    output = capsys.readouterr().out

    assert "Saved Scenarios" in output
    assert "Income Increase" in output


def test_display_ranked_scenarios(
    monkeypatch,
    capsys,
):
    save_result_to_workspace(
        TEST_USER_ID,
        build_result(
            "Smaller Increase",
            3000,
        ),
    )
    save_result_to_workspace(
        TEST_USER_ID,
        build_result(
            "Larger Increase",
            7000,
        ),
    )

    monkeypatch.setattr(
        scenario_workspace_cli,
        "select_ranking_metric",
        lambda: ScenarioRankingMetric.NET_WORTH,
    )

    scenario_workspace_cli.display_ranked_scenarios()

    output = capsys.readouterr().out

    assert "Scenario Ranking" in output
    assert "Larger Increase" in output


def test_remove_saved_scenario(
    monkeypatch,
):
    save_result_to_workspace(
        TEST_USER_ID,
        build_result(
            "Income Increase",
            6500,
        ),
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    scenario_workspace_cli.remove_saved_scenario()

    assert scenario_workspace_cli.get_scenario_workspace(TEST_USER_ID).is_empty()


def test_clear_workspace_flow(
    monkeypatch,
):
    save_result_to_workspace(
        TEST_USER_ID,
        build_result(
            "Income Increase",
            6500,
        ),
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "y",
    )

    scenario_workspace_cli.clear_workspace_flow()

    assert scenario_workspace_cli.get_scenario_workspace(TEST_USER_ID).is_empty()


def test_manage_workspace_returns_on_seven(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "7",
    )

    scenario_workspace_cli.manage_scenario_workspace()
