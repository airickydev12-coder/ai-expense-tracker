import pytest

from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.portfolio import (
    ScenarioPortfolio,
    build_scenario_portfolio,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
)


def build_snapshot() -> dict:
    """Create a baseline financial snapshot."""
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
    *,
    name: str,
    scenario_type: ScenarioType,
    net_worth: float,
    cash_flow: float,
    debt: float = 10000,
) -> ScenarioResult:
    """Create a reusable scenario result."""
    original = build_snapshot()

    projected = {
        **original,
        "net_worth": net_worth,
        "net_cash_flow": cash_flow,
        "total_debt": debt,
    }

    return ScenarioResult(
        scenario_type=scenario_type,
        name=name,
        description="",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot=projected,
        impacts=[],
    )


def build_results() -> list[ScenarioResult]:
    """Create multiple scenario results."""
    return [
        build_result(
            name="Expense Reduction",
            scenario_type=(ScenarioType.EXPENSE_REDUCTION),
            net_worth=1940,
            cash_flow=2120,
        ),
        build_result(
            name="Income Increase",
            scenario_type=(ScenarioType.INCOME_INCREASE),
            net_worth=6500,
            cash_flow=2500,
        ),
        build_result(
            name="Extra Debt Payment",
            scenario_type=(ScenarioType.EXTRA_DEBT_PAYMENT),
            net_worth=900,
            cash_flow=1800,
            debt=7600,
        ),
    ]


def test_create_scenario_portfolio():
    portfolio = ScenarioPortfolio(
        name="Primary Plan",
        results=build_results(),
    )

    assert portfolio.name == "Primary Plan"
    assert len(portfolio.results) == 3


def test_portfolio_rejects_empty_name():
    with pytest.raises(
        ValueError,
        match="name cannot be empty",
    ):
        ScenarioPortfolio(
            name=" ",
            results=[],
        )


def test_portfolio_copies_results():
    results = build_results()

    portfolio = ScenarioPortfolio(
        name="Primary Plan",
        results=results,
    )

    results.clear()

    assert len(portfolio.results) == 3


def test_add_result_returns_new_portfolio():
    portfolio = ScenarioPortfolio(
        name="Primary Plan",
        results=[],
    )

    result = build_results()[0]

    updated = portfolio.add_result(result)

    assert portfolio.results == []
    assert updated.results == [result]


def test_remove_result_returns_new_portfolio():
    portfolio = ScenarioPortfolio(
        name="Primary Plan",
        results=build_results(),
    )

    updated = portfolio.remove_result("Income Increase")

    assert len(portfolio.results) == 3
    assert len(updated.results) == 2
    assert updated.get_result("Income Increase") is None


def test_remove_result_is_case_insensitive():
    portfolio = ScenarioPortfolio(
        name="Primary Plan",
        results=build_results(),
    )

    updated = portfolio.remove_result("income increase")

    assert updated.get_result("Income Increase") is None


def test_get_result():
    portfolio = ScenarioPortfolio(
        name="Primary Plan",
        results=build_results(),
    )

    result = portfolio.get_result("income increase")

    assert result is not None
    assert result.name == "Income Increase"


def test_get_result_returns_none_when_missing():
    portfolio = ScenarioPortfolio(
        name="Primary Plan",
        results=build_results(),
    )

    assert portfolio.get_result("Missing") is None


def test_portfolio_rank():
    portfolio = ScenarioPortfolio(
        name="Primary Plan",
        results=build_results(),
    )

    ranked = portfolio.rank(ScenarioRankingMetric.NET_WORTH)

    assert ranked[0].scenario_name == ("Income Increase")
    assert ranked[1].scenario_name == ("Expense Reduction")


def test_portfolio_best():
    portfolio = ScenarioPortfolio(
        name="Primary Plan",
        results=build_results(),
    )

    best = portfolio.best(ScenarioRankingMetric.DEBT_REDUCTION)

    assert best is not None
    assert best.scenario_name == ("Extra Debt Payment")


def test_empty_portfolio_best_returns_none():
    portfolio = ScenarioPortfolio(
        name="Empty Plan",
        results=[],
    )

    assert portfolio.best() is None


def test_portfolio_serialization():
    portfolio = ScenarioPortfolio(
        name="Primary Plan",
        results=build_results(),
    )

    data = portfolio.to_dict()

    assert data["name"] == "Primary Plan"
    assert len(data["results"]) == 3


def test_build_scenario_portfolio():
    portfolio = build_scenario_portfolio(
        name="Primary Plan",
        results=build_results(),
    )

    assert isinstance(
        portfolio,
        ScenarioPortfolio,
    )
    assert len(portfolio.results) == 3
