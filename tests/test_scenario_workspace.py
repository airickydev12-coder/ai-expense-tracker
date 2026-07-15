from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
)
from src.financial.scenarios.workspace import (
    ScenarioWorkspace,
    clear_scenario_workspace,
    get_saved_scenario_results,
    save_scenario_result,
    scenario_workspace,
)


def build_snapshot() -> dict:
    """Create a baseline snapshot."""
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
    name: str,
    net_worth: float,
) -> ScenarioResult:
    """Create a reusable scenario result."""
    original = build_snapshot()

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
    """Clear shared workspace before every test."""
    clear_scenario_workspace()


def teardown_function():
    """Clear shared workspace after every test."""
    clear_scenario_workspace()


def test_workspace_adds_result():
    workspace = ScenarioWorkspace()

    workspace.add_result(
        build_result(
            "Income Increase",
            6500,
        )
    )

    assert workspace.count() == 1


def test_workspace_replaces_duplicate_name():
    workspace = ScenarioWorkspace()

    workspace.add_result(
        build_result(
            "Income Increase",
            6500,
        )
    )
    workspace.add_result(
        build_result(
            "income increase",
            9000,
        )
    )

    assert workspace.count() == 1
    assert workspace.get_results()[0].projected_snapshot["net_worth"] == 9000


def test_workspace_returns_copy():
    workspace = ScenarioWorkspace()

    workspace.add_result(
        build_result(
            "Income Increase",
            6500,
        )
    )

    returned = workspace.get_results()
    returned.clear()

    assert workspace.count() == 1


def test_workspace_remove_result():
    workspace = ScenarioWorkspace()

    workspace.add_result(
        build_result(
            "Income Increase",
            6500,
        )
    )

    removed = workspace.remove_result("income increase")

    assert removed is not None
    assert workspace.is_empty()


def test_workspace_ranks_results():
    workspace = ScenarioWorkspace()

    workspace.add_result(
        build_result(
            "Smaller Increase",
            3000,
        )
    )
    workspace.add_result(
        build_result(
            "Larger Increase",
            7000,
        )
    )

    ranked = workspace.rank(ScenarioRankingMetric.NET_WORTH)

    assert ranked[0].scenario_name == ("Larger Increase")


def test_workspace_best_result():
    workspace = ScenarioWorkspace()

    workspace.add_result(
        build_result(
            "Smaller Increase",
            3000,
        )
    )
    workspace.add_result(
        build_result(
            "Larger Increase",
            7000,
        )
    )

    best = workspace.best(ScenarioRankingMetric.NET_WORTH)

    assert best is not None
    assert best.scenario_name == ("Larger Increase")


def test_shared_workspace_helpers():
    result = build_result(
        "Income Increase",
        6500,
    )

    save_scenario_result(result)

    assert get_saved_scenario_results() == [result]
    assert scenario_workspace.count() == 1
