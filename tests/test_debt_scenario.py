import pytest

from src.financial.scenarios.debt_scenario import (
    calculate_debt_payoff,
    register_extra_debt_payment_scenario,
    run_extra_debt_payment_scenario,
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
    """Create a snapshot for debt scenario tests."""
    return {
        "total_income": 5000,
        "total_expenses": 3000,
        "net_cash_flow": 2000,
        "total_account_balance": 8000,
        "total_goal_progress": 2500,
        "total_debt": 15000,
        "net_worth": -4500,
        "health_score": 65,
        "health_status": "Fair",
        "debts": [
            {
                "id": 1,
                "name": "Credit Card",
                "balance": 10000,
                "interest_rate": 18,
                "minimum_payment": 300,
            },
            {
                "id": 2,
                "name": "Student Loan",
                "balance": 5000,
                "interest_rate": 4,
                "minimum_payment": 100,
            },
        ],
    }


def setup_function():
    """Reset scenario handlers before each test."""
    reset_scenario_handlers()


def teardown_function():
    """Reset scenario handlers after each test."""
    reset_scenario_handlers()


def test_calculate_debt_payoff():
    projection = calculate_debt_payoff(
        balance=10000,
        annual_interest_rate=18,
        monthly_payment=500,
        horizon_months=12,
    )

    assert projection.payoff_months > 0
    assert projection.payoff_months < 36
    assert projection.total_interest > 0
    assert projection.remaining_balance_at_horizon < 10000


def test_extra_payment_reduces_payoff_time_and_interest():
    baseline = calculate_debt_payoff(
        balance=10000,
        annual_interest_rate=18,
        monthly_payment=300,
        horizon_months=12,
    )

    accelerated = calculate_debt_payoff(
        balance=10000,
        annual_interest_rate=18,
        monthly_payment=500,
        horizon_months=12,
    )

    assert accelerated.payoff_months < baseline.payoff_months
    assert accelerated.total_interest < baseline.total_interest
    assert (
        accelerated.remaining_balance_at_horizon < baseline.remaining_balance_at_horizon
    )


def test_run_extra_debt_payment_scenario():
    result = run_extra_debt_payment_scenario(
        build_snapshot(),
        {
            "debt_id": 1,
            "extra_monthly_payment": 200,
            "horizon_months": 12,
        },
    )

    assert result.scenario_type == ScenarioType.EXTRA_DEBT_PAYMENT
    assert result.name == ("Extra Payment on Credit Card")

    debt_impact = result.get_impact("Selected Debt Balance")
    total_debt_impact = result.get_impact("Total Debt")
    cash_flow_impact = result.get_impact("Monthly Available Cash Flow")
    payoff_impact = result.get_impact("Payoff Months")
    interest_impact = result.get_impact("Lifetime Interest")
    savings_impact = result.get_impact("Lifetime Interest Savings")

    assert debt_impact is not None
    assert debt_impact.original_value == 10000
    assert debt_impact.projected_value < 10000

    assert total_debt_impact is not None
    assert total_debt_impact.projected_value < 15000

    assert cash_flow_impact is not None
    assert cash_flow_impact.projected_value == 1800
    assert cash_flow_impact.change == -200

    assert payoff_impact is not None
    assert payoff_impact.projected_value < (payoff_impact.original_value)

    assert interest_impact is not None
    assert interest_impact.projected_value < (interest_impact.original_value)

    assert savings_impact is not None
    assert savings_impact.projected_value > 0


def test_projected_debt_list_is_updated():
    result = run_extra_debt_payment_scenario(
        build_snapshot(),
        {
            "debt_id": 1,
            "extra_monthly_payment": 200,
            "horizon_months": 12,
        },
    )

    projected_debts = result.projected_snapshot["debts"]

    credit_card = next(debt for debt in projected_debts if debt["id"] == 1)

    student_loan = next(debt for debt in projected_debts if debt["id"] == 2)

    assert credit_card["balance"] < 10000
    assert student_loan["balance"] == 5000


def test_default_horizon_is_twelve_months():
    result = run_extra_debt_payment_scenario(
        build_snapshot(),
        {
            "debt_id": 1,
            "extra_monthly_payment": 200,
        },
    )

    selected_debt_impact = result.get_impact("Selected Debt Balance")

    assert selected_debt_impact is not None
    assert selected_debt_impact.projected_value < 10000


def test_extra_payment_above_cash_flow_adds_risk():
    result = run_extra_debt_payment_scenario(
        build_snapshot(),
        {
            "debt_id": 1,
            "extra_monthly_payment": 2500,
            "horizon_months": 12,
        },
    )

    assert any("exceeds current monthly net cash flow" in risk for risk in result.risks)


def test_negative_cash_flow_adds_risk():
    result = run_extra_debt_payment_scenario(
        build_snapshot(),
        {
            "debt_id": 1,
            "extra_monthly_payment": 2500,
            "horizon_months": 12,
        },
    )

    assert any("negative monthly available cash flow" in risk for risk in result.risks)


def test_low_interest_debt_adds_priority_risk():
    result = run_extra_debt_payment_scenario(
        build_snapshot(),
        {
            "debt_id": 2,
            "extra_monthly_payment": 100,
            "horizon_months": 12,
        },
    )

    assert any("relatively low interest rate" in risk for risk in result.risks)


@pytest.mark.parametrize(
    "amount",
    [
        0,
        -1,
    ],
)
def test_rejects_non_positive_extra_payment(
    amount,
):
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        run_extra_debt_payment_scenario(
            build_snapshot(),
            {
                "debt_id": 1,
                "extra_monthly_payment": amount,
            },
        )


def test_rejects_missing_extra_payment():
    with pytest.raises(
        ValueError,
        match="is required",
    ):
        run_extra_debt_payment_scenario(
            build_snapshot(),
            {
                "debt_id": 1,
            },
        )


def test_rejects_non_numeric_extra_payment():
    with pytest.raises(
        ValueError,
        match="must be a number",
    ):
        run_extra_debt_payment_scenario(
            build_snapshot(),
            {
                "debt_id": 1,
                "extra_monthly_payment": "invalid",
            },
        )


def test_rejects_missing_debt_id():
    with pytest.raises(
        ValueError,
        match="Debt ID is required",
    ):
        run_extra_debt_payment_scenario(
            build_snapshot(),
            {
                "extra_monthly_payment": 200,
            },
        )


def test_rejects_invalid_debt_id():
    with pytest.raises(
        ValueError,
        match="whole number",
    ):
        run_extra_debt_payment_scenario(
            build_snapshot(),
            {
                "debt_id": "invalid",
                "extra_monthly_payment": 200,
            },
        )


def test_rejects_unknown_debt():
    with pytest.raises(
        ValueError,
        match="No debt was found",
    ):
        run_extra_debt_payment_scenario(
            build_snapshot(),
            {
                "debt_id": 999,
                "extra_monthly_payment": 200,
            },
        )


def test_rejects_invalid_horizon():
    with pytest.raises(
        ValueError,
        match="greater than zero months",
    ):
        run_extra_debt_payment_scenario(
            build_snapshot(),
            {
                "debt_id": 1,
                "extra_monthly_payment": 200,
                "horizon_months": 0,
            },
        )


def test_rejects_non_integer_horizon():
    with pytest.raises(
        ValueError,
        match="whole number",
    ):
        run_extra_debt_payment_scenario(
            build_snapshot(),
            {
                "debt_id": 1,
                "extra_monthly_payment": 200,
                "horizon_months": "invalid",
            },
        )


def test_rejects_non_amortizing_minimum_payment():
    snapshot = build_snapshot()
    snapshot["debts"][0]["minimum_payment"] = 100

    with pytest.raises(
        ValueError,
        match="must exceed",
    ):
        run_extra_debt_payment_scenario(
            snapshot,
            {
                "debt_id": 1,
                "extra_monthly_payment": 200,
            },
        )


def test_register_extra_debt_payment_scenario():
    register_extra_debt_payment_scenario()

    assert scenario_service.has_handler(ScenarioType.EXTRA_DEBT_PAYMENT)


def test_run_registered_extra_debt_payment_scenario():
    register_extra_debt_payment_scenario()

    request = ScenarioRequest(
        scenario_type=(ScenarioType.EXTRA_DEBT_PAYMENT),
        name="Credit Card Payoff",
        description=("Pay extra toward the credit card."),
        parameters={
            "debt_id": 1,
            "extra_monthly_payment": 200,
            "horizon_months": 12,
        },
    )

    result = run_financial_scenario(
        request=request,
        snapshot=build_snapshot(),
    )

    assert result.scenario_type == ScenarioType.EXTRA_DEBT_PAYMENT

    payoff_impact = result.get_impact("Payoff Months")

    assert payoff_impact is not None
    assert payoff_impact.change < 0


def test_original_snapshot_is_not_mutated():
    snapshot = build_snapshot()

    run_extra_debt_payment_scenario(
        snapshot,
        {
            "debt_id": 1,
            "extra_monthly_payment": 200,
            "horizon_months": 12,
        },
    )

    assert snapshot["total_debt"] == 15000
    assert snapshot["net_cash_flow"] == 2000
    assert snapshot["net_worth"] == -4500
    assert snapshot["debts"][0]["balance"] == 10000
