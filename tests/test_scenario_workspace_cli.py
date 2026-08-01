from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
)
from src.financial.scenarios.workspace import (
    clear_scenario_workspace,
    save_scenario_result,
)
from src.presentation import scenario_workspace_cli


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


def setup_function():
    """Clear workspace before each test."""
    clear_scenario_workspace()


def teardown_function():
    """Clear workspace after each test."""
    clear_scenario_workspace()


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
    save_scenario_result(
        build_result(
            "Income Increase",
            6500,
        )
    )

    scenario_workspace_cli.display_saved_scenarios()

    output = capsys.readouterr().out

    assert "Saved Scenarios" in output
    assert "Income Increase" in output


def test_display_ranked_scenarios(
    monkeypatch,
    capsys,
):
    save_scenario_result(
        build_result(
            "Smaller Increase",
            3000,
        )
    )
    save_scenario_result(
        build_result(
            "Larger Increase",
            7000,
        )
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
    save_scenario_result(
        build_result(
            "Income Increase",
            6500,
        )
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    scenario_workspace_cli.remove_saved_scenario()

    assert scenario_workspace_cli.get_scenario_workspace().is_empty()


def test_clear_workspace_flow(
    monkeypatch,
):
    save_scenario_result(
        build_result(
            "Income Increase",
            6500,
        )
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "y",
    )

    scenario_workspace_cli.clear_workspace_flow()

    assert scenario_workspace_cli.get_scenario_workspace().is_empty()


def test_manage_workspace_returns_on_seven(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "7",
    )

    scenario_workspace_cli.manage_scenario_workspace()
