from src.financial.coach.coaching import (
    build_coaching_session,
)
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
from src.presentation import coach_cli


def build_snapshot() -> dict:
    """Create a financial snapshot for coach CLI tests."""
    return {
        "total_income": 5000,
        "total_expenses": 3000,
        "net_cash_flow": 2000,
        "total_account_balance": 9000,
        "total_goal_progress": 2500,
        "total_debt": 12000,
        "net_worth": -500,
        "health_score": 68,
        "health_status": "Fair",
        "category_totals": {
            "Housing": 1500,
            "Food": 600,
        },
        "debts": [],
    }


def build_scenario_result() -> ScenarioResult:
    """Create an optimizer scenario result."""
    original = build_snapshot()

    return ScenarioResult(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Increase Income by 10%",
        description="",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot={
            **original,
            "total_income": 5500,
            "net_cash_flow": 2500,
            "total_account_balance": 15000,
            "net_worth": 5500,
            "health_score": 80,
        },
        impacts=[],
        recommendations=["Direct part of the additional income to savings."],
    )


def build_optimizer_result() -> OptimizationResult:
    """Create an optimizer result."""
    scenario = build_scenario_result()

    return OptimizationResult(
        snapshot=build_snapshot(),
        candidates=[],
        successful_results=[scenario],
        ranked_scenarios=rank_scenarios(
            [scenario],
            ScenarioRankingMetric.OVERALL,
        ),
        failures=[],
        ranking_metric=(ScenarioRankingMetric.OVERALL),
    )


def test_build_current_coaching_session(
    monkeypatch,
):
    captured: dict = {}

    monkeypatch.setattr(
        coach_cli,
        "build_current_financial_snapshot",
        build_snapshot,
    )

    def fake_optimize(
        snapshot,
        *,
        ranking_metric,
        limit,
        horizon_months,
    ):
        captured["snapshot"] = snapshot
        captured["ranking_metric"] = ranking_metric
        captured["limit"] = limit
        captured["horizon_months"] = horizon_months

        return build_optimizer_result()

    monkeypatch.setattr(
        coach_cli,
        "optimize_financial_snapshot",
        fake_optimize,
    )

    session = coach_cli.build_current_coaching_session(
        advice_limit=2,
        next_step_limit=4,
        optimization_limit=6,
        horizon_months=18,
    )

    assert captured["ranking_metric"] == ScenarioRankingMetric.OVERALL
    assert captured["limit"] == 6
    assert captured["horizon_months"] == 18
    assert session.financial_health_score == 68
    assert session.advice


def test_run_financial_coach(
    monkeypatch,
):
    captured: dict = {}

    session = build_coaching_session(
        build_snapshot(),
        build_optimizer_result(),
    )

    monkeypatch.setattr(
        coach_cli,
        "build_current_coaching_session",
        lambda: session,
    )

    monkeypatch.setattr(
        coach_cli,
        "display_complete_coaching_session",
        lambda value: captured.update(
            {
                "session": value,
            }
        ),
    )

    coach_cli.run_financial_coach()

    assert captured["session"] == session


def test_run_financial_coach_handles_error(
    monkeypatch,
    capsys,
):
    def fake_build():
        raise ValueError("Unable to generate optimizer candidates.")

    monkeypatch.setattr(
        coach_cli,
        "build_current_coaching_session",
        fake_build,
    )

    coach_cli.run_financial_coach()

    output = capsys.readouterr().out

    assert "Unable to build financial coaching session" in output
    assert "Unable to generate optimizer candidates" in output
