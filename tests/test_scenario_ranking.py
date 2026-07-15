import pytest

from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
    calculate_overall_score,
    calculate_ranking_score,
    get_best_scenario,
    get_debt_reduction,
    get_improvement_count,
    get_metric_change,
    rank_scenarios,
)
from src.financial.scenarios.report import (
    build_scenario_comparison_report,
)


def build_base_snapshot() -> dict:
    """Create a shared baseline snapshot."""
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


def build_income_result() -> ScenarioResult:
    """Create an income-increase result."""
    original = build_base_snapshot()

    projected = {
        **original,
        "total_income": 5500,
        "net_cash_flow": 2500,
        "total_account_balance": 14000,
        "net_worth": 6500,
    }

    return ScenarioResult(
        scenario_type=ScenarioType.INCOME_INCREASE,
        name="Income Increase",
        description="Increase income by ten percent.",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot=projected,
        impacts=[],
    )


def build_expense_result() -> ScenarioResult:
    """Create an expense-reduction result."""
    original = build_base_snapshot()

    projected = {
        **original,
        "total_expenses": 2880,
        "net_cash_flow": 2120,
        "total_account_balance": 9440,
        "net_worth": 1940,
    }

    return ScenarioResult(
        scenario_type=(ScenarioType.EXPENSE_REDUCTION),
        name="Expense Reduction",
        description="Reduce expenses.",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot=projected,
        impacts=[],
    )


def build_debt_result() -> ScenarioResult:
    """Create an extra-debt-payment result."""
    original = build_base_snapshot()

    projected = {
        **original,
        "net_cash_flow": 1800,
        "total_debt": 7600,
        "net_worth": 900,
    }

    return ScenarioResult(
        scenario_type=(ScenarioType.EXTRA_DEBT_PAYMENT),
        name="Extra Debt Payment",
        description="Pay extra toward debt.",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot=projected,
        impacts=[],
    )


def test_get_metric_change():
    report = build_scenario_comparison_report(build_income_result())

    assert (
        get_metric_change(
            report,
            "Net Worth",
        )
        == 6000
    )


def test_get_metric_change_returns_zero_when_missing():
    report = build_scenario_comparison_report(build_income_result())

    assert (
        get_metric_change(
            report,
            "Unknown Metric",
        )
        == 0
    )


def test_get_debt_reduction():
    report = build_scenario_comparison_report(build_debt_result())

    assert get_debt_reduction(report) == 2400


def test_get_improvement_count():
    report = build_scenario_comparison_report(build_expense_result())

    assert get_improvement_count(report) == 4


def test_calculate_net_worth_ranking_score():
    report = build_scenario_comparison_report(build_income_result())

    score = calculate_ranking_score(
        report,
        ScenarioRankingMetric.NET_WORTH,
    )

    assert score == 6000


def test_calculate_cash_flow_ranking_score():
    report = build_scenario_comparison_report(build_income_result())

    score = calculate_ranking_score(
        report,
        ScenarioRankingMetric.CASH_FLOW,
    )

    assert score == 500


def test_calculate_debt_reduction_score():
    report = build_scenario_comparison_report(build_debt_result())

    score = calculate_ranking_score(
        report,
        ScenarioRankingMetric.DEBT_REDUCTION,
    )

    assert score == 2400


def test_calculate_improvement_count_score():
    report = build_scenario_comparison_report(build_expense_result())

    score = calculate_ranking_score(
        report,
        ScenarioRankingMetric.IMPROVEMENT_COUNT,
    )

    assert score == 4


def test_calculate_overall_score_rewards_improvements():
    report = build_scenario_comparison_report(build_income_result())

    score = calculate_overall_score(report)

    assert score > 0


def test_rank_scenarios_by_net_worth():
    ranked = rank_scenarios(
        [
            build_expense_result(),
            build_income_result(),
            build_debt_result(),
        ],
        ScenarioRankingMetric.NET_WORTH,
    )

    assert ranked[0].scenario_name == ("Income Increase")
    assert ranked[0].score == 6000
    assert ranked[1].scenario_name == ("Expense Reduction")
    assert ranked[2].scenario_name == ("Extra Debt Payment")


def test_rank_scenarios_by_cash_flow():
    ranked = rank_scenarios(
        [
            build_debt_result(),
            build_expense_result(),
            build_income_result(),
        ],
        ScenarioRankingMetric.CASH_FLOW,
    )

    assert ranked[0].scenario_name == ("Income Increase")
    assert ranked[-1].scenario_name == ("Extra Debt Payment")


def test_rank_scenarios_by_debt_reduction():
    ranked = rank_scenarios(
        [
            build_income_result(),
            build_debt_result(),
            build_expense_result(),
        ],
        ScenarioRankingMetric.DEBT_REDUCTION,
    )

    assert ranked[0].scenario_name == ("Extra Debt Payment")
    assert ranked[0].score == 2400


def test_rank_scenarios_assigns_sequential_ranks():
    ranked = rank_scenarios(
        [
            build_income_result(),
            build_expense_result(),
            build_debt_result(),
        ]
    )

    assert [item.rank for item in ranked] == [
        1,
        2,
        3,
    ]


def test_rank_scenarios_resolves_ties_by_name():
    first = build_expense_result()

    second = ScenarioResult(
        scenario_type=(ScenarioType.EXPENSE_REDUCTION),
        name="Another Expense Reduction",
        description="",
        assumptions=[],
        original_snapshot=(first.original_snapshot),
        projected_snapshot=(first.projected_snapshot),
        impacts=[],
    )

    ranked = rank_scenarios(
        [
            first,
            second,
        ],
        ScenarioRankingMetric.NET_WORTH,
    )

    assert ranked[0].scenario_name == ("Another Expense Reduction")
    assert ranked[1].scenario_name == ("Expense Reduction")


def test_get_best_scenario():
    best = get_best_scenario(
        [
            build_expense_result(),
            build_income_result(),
            build_debt_result(),
        ],
        ScenarioRankingMetric.NET_WORTH,
    )

    assert best is not None
    assert best.scenario_name == "Income Increase"


def test_get_best_scenario_returns_none_when_empty():
    assert get_best_scenario([]) is None


def test_ranked_scenario_serialization():
    ranked = rank_scenarios(
        [
            build_income_result(),
        ]
    )

    data = ranked[0].to_dict()

    assert data["rank"] == 1
    assert data["scenario_name"] == "Income Increase"
    assert data["ranking_metric"] == "Overall"
    assert "result" in data
    assert "report" in data
