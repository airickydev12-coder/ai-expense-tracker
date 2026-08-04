from decimal import Decimal

from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.optimizer import (
    OptimizationResult,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
    rank_scenarios,
)
from src.presentation import optimizer_cli


def build_snapshot() -> dict:
    """Create a snapshot for optimizer CLI tests."""
    return {
        "total_income": Decimal("5000.00"),
        "total_expenses": Decimal("3000.00"),
        "net_cash_flow": Decimal("2000.00"),
        "total_account_balance": Decimal("8000.00"),
        "total_goal_progress": Decimal("2500.00"),
        "total_debt": Decimal("10000.00"),
        "net_worth": Decimal("500.00"),
        "health_score": 70,
        "health_status": "Good",
        "category_totals": {
            "Food": Decimal("600.00"),
        },
        "debts": [
            {
                "id": 1,
                "name": "Credit Card",
                "balance": Decimal("10000.00"),
                "interest_rate": 18,
                "minimum_payment": Decimal("300.00"),
            }
        ],
    }


def build_result() -> ScenarioResult:
    """Create a scenario result for optimizer tests."""
    original = build_snapshot()

    projected = {
        **original,
        "total_income": Decimal("5500.00"),
        "net_cash_flow": Decimal("2500.00"),
        "total_account_balance": Decimal("14000.00"),
        "net_worth": Decimal("6500.00"),
        "health_score": 82,
    }

    return ScenarioResult(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Increase Income by 10%",
        description="Increase monthly income.",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot=projected,
        impacts=[],
    )


def build_optimization_result(
    ranking_metric: ScenarioRankingMetric = (ScenarioRankingMetric.OVERALL),
) -> OptimizationResult:
    """Create an optimizer result for CLI tests."""
    scenario_result = build_result()

    ranked = rank_scenarios(
        [
            scenario_result,
        ],
        ranking_metric,
    )

    return OptimizationResult(
        snapshot=build_snapshot(),
        candidates=[],
        successful_results=[
            scenario_result,
        ],
        ranked_scenarios=ranked,
        failures=[],
        ranking_metric=ranking_metric,
    )


def test_run_optimizer(
    monkeypatch,
):
    captured: dict = {}

    inputs = iter(
        [
            "12",
            "5",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        optimizer_cli,
        "get_cli_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        optimizer_cli,
        "build_current_financial_snapshot",
        lambda user_id: build_snapshot(),
    )

    def fake_optimize(
        snapshot,
        *,
        ranking_metric,
        horizon_months,
        limit,
    ):
        captured["snapshot"] = snapshot
        captured["ranking_metric"] = ranking_metric
        captured["horizon_months"] = horizon_months
        captured["limit"] = limit

        return build_optimization_result(ranking_metric)

    monkeypatch.setattr(
        optimizer_cli,
        "optimize_financial_snapshot",
        fake_optimize,
    )

    monkeypatch.setattr(
        optimizer_cli,
        "display_optimizer_result",
        lambda result: captured.update(
            {
                "result": result,
            }
        ),
    )

    result = optimizer_cli._run_optimizer(ScenarioRankingMetric.NET_WORTH)

    assert result is not None
    assert captured["ranking_metric"] == ScenarioRankingMetric.NET_WORTH
    assert captured["horizon_months"] == 12
    assert captured["limit"] == 5
    assert captured["result"] == result


def test_run_optimizer_uses_defaults(
    monkeypatch,
):
    captured: dict = {}

    inputs = iter(
        [
            "",
            "",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        optimizer_cli,
        "get_cli_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        optimizer_cli,
        "build_current_financial_snapshot",
        lambda user_id: build_snapshot(),
    )

    def fake_optimize(
        snapshot,
        *,
        ranking_metric,
        horizon_months,
        limit,
    ):
        captured["horizon_months"] = horizon_months
        captured["limit"] = limit

        return build_optimization_result(ranking_metric)

    monkeypatch.setattr(
        optimizer_cli,
        "optimize_financial_snapshot",
        fake_optimize,
    )

    monkeypatch.setattr(
        optimizer_cli,
        "display_optimizer_result",
        lambda result: None,
    )

    optimizer_cli._run_optimizer(ScenarioRankingMetric.OVERALL)

    assert captured["horizon_months"] == 12
    assert captured["limit"] == 5


def test_run_optimizer_handles_error(
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "12",
            "5",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        optimizer_cli,
        "get_cli_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        optimizer_cli,
        "build_current_financial_snapshot",
        lambda user_id: build_snapshot(),
    )

    def fake_optimize(
        snapshot,
        *,
        ranking_metric,
        horizon_months,
        limit,
    ):
        raise ValueError("Unable to evaluate candidates.")

    monkeypatch.setattr(
        optimizer_cli,
        "optimize_financial_snapshot",
        fake_optimize,
    )

    result = optimizer_cli._run_optimizer(ScenarioRankingMetric.OVERALL)

    output = capsys.readouterr().out

    assert result is None
    assert "Unable to optimize financial plan" in output
    assert "Unable to evaluate candidates" in output


def test_save_best_optimizer_result(
    monkeypatch,
):
    captured: dict = {}

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "y",
    )

    monkeypatch.setattr(
        optimizer_cli,
        "get_cli_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        optimizer_cli,
        "save_result_to_workspace",
        lambda user_id, result: captured.update(
            {
                "saved_result": result,
            }
        ),
    )

    result = build_optimization_result()

    optimizer_cli.save_best_optimizer_result(result)

    assert result.best_scenario is not None
    assert captured["saved_result"] == result.best_scenario.result

    assert captured["saved_result"] == result.best_scenario.result


def test_save_best_optimizer_result_declined(
    monkeypatch,
    capsys,
):
    captured = {
        "saved": False,
    }

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "n",
    )

    monkeypatch.setattr(
        optimizer_cli,
        "save_result_to_workspace",
        lambda result: captured.update(
            {
                "saved": True,
            }
        ),
    )

    optimizer_cli.save_best_optimizer_result(build_optimization_result())

    output = capsys.readouterr().out

    assert captured["saved"] is False
    assert "was not saved" in output


def test_manage_optimizer_routes_debt(
    monkeypatch,
):
    captured: dict = {}

    choices = iter(
        [
            "4",
            "7",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(choices),
    )

    monkeypatch.setattr(
        optimizer_cli,
        "display_optimizer_menu",
        lambda: None,
    )

    def fake_flow(ranking_metric):
        captured["ranking_metric"] = ranking_metric

    monkeypatch.setattr(
        optimizer_cli,
        "run_optimizer_flow",
        fake_flow,
    )

    optimizer_cli.manage_optimizer()

    assert captured["ranking_metric"] == ScenarioRankingMetric.DEBT_REDUCTION


def test_manage_optimizer_routes_lowest_risk(
    monkeypatch,
):
    captured: dict = {}

    choices = iter(
        [
            "5",
            "7",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(choices),
    )

    monkeypatch.setattr(
        optimizer_cli,
        "display_optimizer_menu",
        lambda: None,
    )

    monkeypatch.setattr(
        optimizer_cli,
        "run_optimizer_flow",
        lambda metric: captured.update(
            {
                "ranking_metric": metric,
            }
        ),
    )

    optimizer_cli.manage_optimizer()

    assert captured["ranking_metric"] == ScenarioRankingMetric.LOWEST_RISK


def test_manage_optimizer_returns_on_seven(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "7",
    )

    optimizer_cli.manage_optimizer()
