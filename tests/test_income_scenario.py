import pytest

from src.financial.scenarios.income_scenario import (
    register_income_increase_scenario,
    run_income_increase_scenario,
)
from src.financial.scenarios.models import (
    ScenarioRequest,
    ScenarioType,
)
from src.financial.scenarios.service import (
    reset_scenario_handlers,
    run_financial_scenario,
    scenario_service,
)


def build_snapshot() -> dict:
    """Create a snapshot for income-scenario tests."""
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


def setup_function():
    """Reset handlers before every test."""
    reset_scenario_handlers()


def teardown_function():
    """Reset handlers after every test."""
    reset_scenario_handlers()


def test_run_income_increase_scenario():
    result = run_income_increase_scenario(
        build_snapshot(),
        {
            "increase_percentage": 10,
            "horizon_months": 12,
        },
    )

    assert result.scenario_type == ScenarioType.INCOME_INCREASE

    income_impact = result.get_impact("Total Income")
    cash_flow_impact = result.get_impact("Net Cash Flow")
    balance_impact = result.get_impact("Account Balance")
    net_worth_impact = result.get_impact("Net Worth")
    annual_income_impact = result.get_impact("Annual Income Increase")
    savings_rate_impact = result.get_impact("Savings Rate")

    assert income_impact is not None
    assert income_impact.original_value == 5000
    assert income_impact.projected_value == 5500
    assert income_impact.change == 500

    assert cash_flow_impact is not None
    assert cash_flow_impact.projected_value == 2500
    assert cash_flow_impact.change == 500

    assert balance_impact is not None
    assert balance_impact.projected_value == 14000
    assert balance_impact.change == 6000

    assert net_worth_impact is not None
    assert net_worth_impact.projected_value == 6500
    assert net_worth_impact.change == 6000

    assert annual_income_impact is not None
    assert annual_income_impact.projected_value == 6000

    assert savings_rate_impact is not None
    assert savings_rate_impact.original_value == pytest.approx(40)
    assert savings_rate_impact.projected_value == pytest.approx(45.454545)


def test_projected_snapshot_is_updated():
    result = run_income_increase_scenario(
        build_snapshot(),
        {
            "increase_percentage": 20,
            "horizon_months": 6,
        },
    )

    projected = result.projected_snapshot

    assert projected["total_income"] == 6000
    assert projected["total_expenses"] == 3000
    assert projected["net_cash_flow"] == 3000
    assert projected["total_account_balance"] == 14000
    assert projected["net_worth"] == 6500


def test_default_horizon_is_twelve_months():
    result = run_income_increase_scenario(
        build_snapshot(),
        {
            "increase_percentage": 10,
        },
    )

    net_worth_impact = result.get_impact("Net Worth")

    assert net_worth_impact is not None
    assert net_worth_impact.change == 6000


def test_large_income_increase_adds_risk():
    result = run_income_increase_scenario(
        build_snapshot(),
        {
            "increase_percentage": 50,
            "horizon_months": 12,
        },
    )

    assert any("major career or business change" in risk for risk in result.risks)


@pytest.mark.parametrize(
    "percentage",
    [
        0,
        -1,
    ],
)
def test_rejects_non_positive_percentage(
    percentage,
):
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        run_income_increase_scenario(
            build_snapshot(),
            {
                "increase_percentage": percentage,
            },
        )


def test_rejects_percentage_above_limit():
    with pytest.raises(
        ValueError,
        match="cannot exceed 500",
    ):
        run_income_increase_scenario(
            build_snapshot(),
            {
                "increase_percentage": 501,
            },
        )


def test_rejects_missing_percentage():
    with pytest.raises(
        ValueError,
        match="is required",
    ):
        run_income_increase_scenario(
            build_snapshot(),
            {},
        )


def test_rejects_non_numeric_percentage():
    with pytest.raises(
        ValueError,
        match="must be a number",
    ):
        run_income_increase_scenario(
            build_snapshot(),
            {
                "increase_percentage": "invalid",
            },
        )


def test_rejects_invalid_horizon():
    with pytest.raises(
        ValueError,
        match="greater than zero months",
    ):
        run_income_increase_scenario(
            build_snapshot(),
            {
                "increase_percentage": 10,
                "horizon_months": 0,
            },
        )


def test_rejects_non_integer_horizon():
    with pytest.raises(
        ValueError,
        match="whole number",
    ):
        run_income_increase_scenario(
            build_snapshot(),
            {
                "increase_percentage": 10,
                "horizon_months": "invalid",
            },
        )


def test_register_income_increase_scenario():
    register_income_increase_scenario()

    assert scenario_service.has_handler(ScenarioType.INCOME_INCREASE)


def test_run_registered_income_increase_scenario():
    register_income_increase_scenario()

    request = ScenarioRequest(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Raise Scenario",
        description="Model a ten percent raise.",
        parameters={
            "increase_percentage": 10,
            "horizon_months": 12,
        },
    )

    result = run_financial_scenario(
        request=request,
        snapshot=build_snapshot(),
    )

    assert result.scenario_type == ScenarioType.INCOME_INCREASE
    assert result.projected_snapshot["total_income"] == 5500


def test_original_snapshot_is_not_mutated():
    snapshot = build_snapshot()

    run_income_increase_scenario(
        snapshot,
        {
            "increase_percentage": 10,
            "horizon_months": 12,
        },
    )

    assert snapshot["total_income"] == 5000
    assert snapshot["net_cash_flow"] == 2000
    assert snapshot["total_account_balance"] == 8000
    assert snapshot["net_worth"] == 500
