from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
    build_ranking_reason,
    calculate_overall_score,
    calculate_ranking_score,
    get_best_scenario,
    get_debt_reduction,
    get_improvement_count,
    get_metric_change,
    get_most_sustainable_scenario,
    get_risk_ranking_score,
    get_safest_scenario,
    get_sustainability_ranking_score,
    rank_scenarios,
)
from src.financial.scenarios.report import (
    build_scenario_comparison_report,
)
from src.financial.scenarios.scoring import (
    RiskLevel,
    SustainabilityLevel,
    score_scenario_result,
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
        "health_score": 82,
    }

    return ScenarioResult(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Income Increase",
        description=("Increase income by ten percent."),
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
        "health_score": 75,
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
        "health_score": 74,
    }

    return ScenarioResult(
        scenario_type=(ScenarioType.EXTRA_DEBT_PAYMENT),
        name="Extra Debt Payment",
        description="Pay extra toward debt.",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot=projected,
        impacts=[],
        risks=["The extra payment reduces monthly " "available cash flow."],
    )


def build_risky_result() -> ScenarioResult:
    """Create a high-risk scenario result."""
    original = build_base_snapshot()

    projected = {
        **original,
        "net_cash_flow": -500,
        "total_account_balance": 4000,
        "total_debt": 11000,
        "net_worth": -6500,
        "health_score": 40,
    }

    return ScenarioResult(
        scenario_type=(ScenarioType.ADDITIONAL_SAVINGS),
        name="Overcommitted Savings",
        description="Save more than available cash flow.",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot=projected,
        impacts=[],
        risks=[
            "The plan creates negative cash flow.",
            "The savings target is not sustainable.",
        ],
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

    assert get_improvement_count(report) == 5


def test_get_risk_ranking_score():
    assert get_risk_ranking_score(RiskLevel.LOW) == 4

    assert get_risk_ranking_score(RiskLevel.MODERATE) == 3

    assert get_risk_ranking_score(RiskLevel.HIGH) == 2

    assert get_risk_ranking_score(RiskLevel.CRITICAL) == 1


def test_get_sustainability_ranking_score():
    assert get_sustainability_ranking_score(SustainabilityLevel.EXCELLENT) == 4

    assert get_sustainability_ranking_score(SustainabilityLevel.GOOD) == 3

    assert get_sustainability_ranking_score(SustainabilityLevel.FAIR) == 2

    assert get_sustainability_ranking_score(SustainabilityLevel.POOR) == 1


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

    assert score == 5


def test_calculate_lowest_risk_score():
    result = build_income_result()

    report = build_scenario_comparison_report(result)

    scenario_score = score_scenario_result(result)

    score = calculate_ranking_score(
        report,
        ScenarioRankingMetric.LOWEST_RISK,
        scenario_score,
    )

    assert score == 4


def test_calculate_sustainability_score():
    result = build_income_result()

    report = build_scenario_comparison_report(result)

    scenario_score = score_scenario_result(result)

    score = calculate_ranking_score(
        report,
        ScenarioRankingMetric.SUSTAINABILITY,
        scenario_score,
    )

    assert score == 4


def test_calculate_overall_score_rewards_improvements():
    report = build_scenario_comparison_report(build_income_result())

    score = calculate_overall_score(report)

    assert score > 0


def test_overall_ranking_uses_scenario_score():
    result = build_income_result()

    report = build_scenario_comparison_report(result)

    scenario_score = score_scenario_result(result)

    ranking_score = calculate_ranking_score(
        report,
        ScenarioRankingMetric.OVERALL,
        scenario_score,
    )

    assert ranking_score == scenario_score.overall_score


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


def test_rank_scenarios_by_overall_score():
    ranked = rank_scenarios(
        [
            build_debt_result(),
            build_expense_result(),
            build_income_result(),
        ],
        ScenarioRankingMetric.OVERALL,
    )

    assert ranked[0].scenario_name == ("Income Increase")

    assert ranked[0].score == ranked[0].scenario_score.overall_score


def test_rank_scenarios_by_lowest_risk():
    ranked = rank_scenarios(
        [
            build_risky_result(),
            build_income_result(),
        ],
        ScenarioRankingMetric.LOWEST_RISK,
    )

    assert ranked[0].scenario_name == ("Income Increase")

    assert ranked[-1].scenario_name == "Overcommitted Savings"


def test_rank_scenarios_by_sustainability():
    ranked = rank_scenarios(
        [
            build_risky_result(),
            build_income_result(),
        ],
        ScenarioRankingMetric.SUSTAINABILITY,
    )

    assert ranked[0].scenario_name == ("Income Increase")

    assert ranked[0].scenario_score.sustainability == SustainabilityLevel.EXCELLENT


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


def test_ranking_reason_for_overall_score():
    result = build_income_result()

    report = build_scenario_comparison_report(result)

    scenario_score = score_scenario_result(result)

    reason = build_ranking_reason(
        ranking_metric=(ScenarioRankingMetric.OVERALL),
        score=scenario_score.overall_score,
        report=report,
        scenario_score=scenario_score,
    )

    assert "Overall plan score" in reason
    assert "/100" in reason


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
    assert best.scenario_name == ("Income Increase")


def test_get_best_scenario_returns_none_when_empty():
    assert get_best_scenario([]) is None


def test_get_safest_scenario():
    safest = get_safest_scenario(
        [
            build_risky_result(),
            build_income_result(),
        ]
    )

    assert safest is not None
    assert safest.scenario_name == ("Income Increase")


def test_get_most_sustainable_scenario():
    sustainable = get_most_sustainable_scenario(
        [
            build_risky_result(),
            build_income_result(),
        ]
    )

    assert sustainable is not None
    assert sustainable.scenario_name == ("Income Increase")


def test_ranked_scenario_serialization():
    ranked = rank_scenarios(
        [
            build_income_result(),
        ]
    )

    data = ranked[0].to_dict()

    assert data["rank"] == 1
    assert data["scenario_name"] == ("Income Increase")
    assert data["ranking_metric"] == "Overall"
    assert "reason" in data
    assert "scenario_score" in data
    assert "result" in data
    assert "report" in data
