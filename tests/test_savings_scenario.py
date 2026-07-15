import pytest

from src.financial.scenarios.models import (
    ScenarioRequest,
    ScenarioType,
)
from src.financial.scenarios.savings_scenario import (
    register_additional_savings_scenario,
    run_additional_savings_scenario,
)
from src.financial.scenarios.service import (
    reset_scenario_handlers,
    run_financial_scenario,
    scenario_service,
)


def build_snapshot() -> dict:
    """Create a snapshot for savings-scenario tests."""
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


def test_run_additional_savings_scenario():
    result = run_additional_savings_scenario(
        build_snapshot(),
        {
            "additional_monthly_savings": 500,
            "horizon_months": 12,
        },
    )

    assert result.scenario_type == ScenarioType.ADDITIONAL_SAVINGS

    cash_flow_impact = result.get_impact("Monthly Available Cash Flow")
    balance_impact = result.get_impact("Account Balance")
    goal_impact = result.get_impact("Goal Progress")
    net_worth_impact = result.get_impact("Net Worth")
    annual_savings_impact = result.get_impact("Annual Additional Savings")
    savings_rate_impact = result.get_impact("Savings Rate")

    assert cash_flow_impact is not None
    assert cash_flow_impact.original_value == 2000
    assert cash_flow_impact.projected_value == 1500
    assert cash_flow_impact.change == -500

    assert balance_impact is not None
    assert balance_impact.projected_value == 14000
    assert balance_impact.change == 6000

    assert goal_impact is not None
    assert goal_impact.projected_value == 8500
    assert goal_impact.change == 6000

    assert net_worth_impact is not None
    assert net_worth_impact.projected_value == 6500
    assert net_worth_impact.change == 6000

    assert annual_savings_impact is not None
    assert annual_savings_impact.projected_value == 6000

    assert savings_rate_impact is not None
    assert savings_rate_impact.original_value == pytest.approx(40)
    assert savings_rate_impact.projected_value == pytest.approx(50)


def test_projected_snapshot_is_updated():
    result = run_additional_savings_scenario(
        build_snapshot(),
        {
            "additional_monthly_savings": 300,
            "horizon_months": 6,
        },
    )

    projected = result.projected_snapshot

    assert projected["total_income"] == 5000
    assert projected["total_expenses"] == 3000
    assert projected["net_cash_flow"] == 1700
    assert projected["total_account_balance"] == 9800
    assert projected["total_goal_progress"] == 4300
    assert projected["net_worth"] == 2300


def test_default_horizon_is_twelve_months():
    result = run_additional_savings_scenario(
        build_snapshot(),
        {
            "additional_monthly_savings": 250,
        },
    )

    net_worth_impact = result.get_impact("Net Worth")

    assert net_worth_impact is not None
    assert net_worth_impact.change == 3000


def test_savings_above_cash_flow_adds_risk():
    result = run_additional_savings_scenario(
        build_snapshot(),
        {
            "additional_monthly_savings": 2500,
            "horizon_months": 12,
        },
    )

    assert any("exceeds current monthly net cash flow" in risk for risk in result.risks)


def test_negative_projected_cash_flow_adds_risk():
    result = run_additional_savings_scenario(
        build_snapshot(),
        {
            "additional_monthly_savings": 2500,
            "horizon_months": 12,
        },
    )

    assert any("negative monthly available cash flow" in risk for risk in result.risks)


@pytest.mark.parametrize(
    "amount",
    [
        0,
        -1,
    ],
)
def test_rejects_non_positive_savings_amount(
    amount,
):
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        run_additional_savings_scenario(
            build_snapshot(),
            {
                "additional_monthly_savings": amount,
            },
        )


def test_rejects_missing_savings_amount():
    with pytest.raises(
        ValueError,
        match="is required",
    ):
        run_additional_savings_scenario(
            build_snapshot(),
            {},
        )


def test_rejects_non_numeric_savings_amount():
    with pytest.raises(
        ValueError,
        match="must be a number",
    ):
        run_additional_savings_scenario(
            build_snapshot(),
            {
                "additional_monthly_savings": "invalid",
            },
        )


def test_rejects_invalid_horizon():
    with pytest.raises(
        ValueError,
        match="greater than zero months",
    ):
        run_additional_savings_scenario(
            build_snapshot(),
            {
                "additional_monthly_savings": 500,
                "horizon_months": 0,
            },
        )


def test_rejects_non_integer_horizon():
    with pytest.raises(
        ValueError,
        match="whole number",
    ):
        run_additional_savings_scenario(
            build_snapshot(),
            {
                "additional_monthly_savings": 500,
                "horizon_months": "invalid",
            },
        )


def test_register_additional_savings_scenario():
    register_additional_savings_scenario()

    assert scenario_service.has_handler(ScenarioType.ADDITIONAL_SAVINGS)


def test_run_registered_additional_savings_scenario():
    register_additional_savings_scenario()

    request = ScenarioRequest(
        scenario_type=(ScenarioType.ADDITIONAL_SAVINGS),
        name="Save More",
        description=("Save an additional amount each month."),
        parameters={
            "additional_monthly_savings": 500,
            "horizon_months": 12,
        },
    )

    result = run_financial_scenario(
        request=request,
        snapshot=build_snapshot(),
    )

    assert result.scenario_type == ScenarioType.ADDITIONAL_SAVINGS
    assert result.projected_snapshot["total_account_balance"] == 14000


def test_original_snapshot_is_not_mutated():
    snapshot = build_snapshot()

    run_additional_savings_scenario(
        snapshot,
        {
            "additional_monthly_savings": 500,
            "horizon_months": 12,
        },
    )

    assert snapshot["net_cash_flow"] == 2000
    assert snapshot["total_account_balance"] == 8000
    assert snapshot["total_goal_progress"] == 2500
    assert snapshot["net_worth"] == 500
