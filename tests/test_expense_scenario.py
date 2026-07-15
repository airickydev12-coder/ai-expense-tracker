import pytest

from src.financial.scenarios.expense_scenario import (
    register_expense_reduction_scenario,
    run_expense_reduction_scenario,
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
    """Create a snapshot for expense-reduction tests."""
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
        "category_totals": {
            "Food": 600,
            "Housing": 1500,
            "Transportation": 400,
            "Other": 500,
        },
    }


def setup_function():
    """Reset scenario handlers before every test."""
    reset_scenario_handlers()


def teardown_function():
    """Reset scenario handlers after every test."""
    reset_scenario_handlers()


def test_run_expense_reduction_scenario():
    result = run_expense_reduction_scenario(
        build_snapshot(),
        {
            "category": "Food",
            "reduction_percentage": 20,
            "horizon_months": 12,
        },
    )

    assert result.scenario_type == ScenarioType.EXPENSE_REDUCTION
    assert result.name == "Food Expense Reduction"

    category_impact = result.get_impact("Category Spending")
    expense_impact = result.get_impact("Total Expenses")
    cash_flow_impact = result.get_impact("Net Cash Flow")
    balance_impact = result.get_impact("Account Balance")
    net_worth_impact = result.get_impact("Net Worth")
    annual_savings_impact = result.get_impact("Annual Savings")

    assert category_impact is not None
    assert category_impact.original_value == 600
    assert category_impact.projected_value == 480
    assert category_impact.change == -120

    assert expense_impact is not None
    assert expense_impact.projected_value == 2880
    assert expense_impact.change == -120

    assert cash_flow_impact is not None
    assert cash_flow_impact.projected_value == 2120
    assert cash_flow_impact.change == 120

    assert balance_impact is not None
    assert balance_impact.projected_value == 9440
    assert balance_impact.change == 1440

    assert net_worth_impact is not None
    assert net_worth_impact.projected_value == 1940
    assert net_worth_impact.change == 1440

    assert annual_savings_impact is not None
    assert annual_savings_impact.projected_value == 1440


def test_projected_snapshot_is_updated():
    result = run_expense_reduction_scenario(
        build_snapshot(),
        {
            "category": "Food",
            "reduction_percentage": 25,
            "horizon_months": 6,
        },
    )

    projected = result.projected_snapshot

    assert projected["total_expenses"] == 2850
    assert projected["net_cash_flow"] == 2150
    assert projected["total_account_balance"] == 8900
    assert projected["net_worth"] == 1400
    assert projected["category_totals"]["Food"] == 450


def test_category_matching_is_case_insensitive():
    result = run_expense_reduction_scenario(
        build_snapshot(),
        {
            "category": "food",
            "reduction_percentage": 10,
        },
    )

    category_impact = result.get_impact("Category Spending")

    assert category_impact is not None
    assert category_impact.projected_value == 540


def test_default_horizon_is_twelve_months():
    result = run_expense_reduction_scenario(
        build_snapshot(),
        {
            "category": "Food",
            "reduction_percentage": 10,
        },
    )

    balance_impact = result.get_impact("Account Balance")

    assert balance_impact is not None
    assert balance_impact.change == 720


def test_large_reduction_adds_risk():
    result = run_expense_reduction_scenario(
        build_snapshot(),
        {
            "category": "Food",
            "reduction_percentage": 50,
            "horizon_months": 12,
        },
    )

    assert any("difficult to maintain" in risk for risk in result.risks)


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
        run_expense_reduction_scenario(
            build_snapshot(),
            {
                "category": "Food",
                "reduction_percentage": percentage,
            },
        )


def test_rejects_percentage_above_one_hundred():
    with pytest.raises(
        ValueError,
        match="cannot exceed 100",
    ):
        run_expense_reduction_scenario(
            build_snapshot(),
            {
                "category": "Food",
                "reduction_percentage": 101,
            },
        )


def test_rejects_missing_percentage():
    with pytest.raises(
        ValueError,
        match="Reduction percentage is required",
    ):
        run_expense_reduction_scenario(
            build_snapshot(),
            {
                "category": "Food",
            },
        )


def test_rejects_non_numeric_percentage():
    with pytest.raises(
        ValueError,
        match="must be a number",
    ):
        run_expense_reduction_scenario(
            build_snapshot(),
            {
                "category": "Food",
                "reduction_percentage": "invalid",
            },
        )


def test_rejects_missing_category():
    with pytest.raises(
        ValueError,
        match="Expense category is required",
    ):
        run_expense_reduction_scenario(
            build_snapshot(),
            {
                "reduction_percentage": 20,
            },
        )


def test_rejects_unknown_category():
    with pytest.raises(
        ValueError,
        match="No spending was found",
    ):
        run_expense_reduction_scenario(
            build_snapshot(),
            {
                "category": "Travel",
                "reduction_percentage": 20,
            },
        )


def test_rejects_invalid_horizon():
    with pytest.raises(
        ValueError,
        match="greater than zero months",
    ):
        run_expense_reduction_scenario(
            build_snapshot(),
            {
                "category": "Food",
                "reduction_percentage": 20,
                "horizon_months": 0,
            },
        )


def test_rejects_non_integer_horizon():
    with pytest.raises(
        ValueError,
        match="whole number",
    ):
        run_expense_reduction_scenario(
            build_snapshot(),
            {
                "category": "Food",
                "reduction_percentage": 20,
                "horizon_months": "invalid",
            },
        )


def test_register_expense_reduction_scenario():
    register_expense_reduction_scenario()

    assert scenario_service.has_handler(ScenarioType.EXPENSE_REDUCTION)


def test_run_registered_expense_reduction_scenario():
    register_expense_reduction_scenario()

    request = ScenarioRequest(
        scenario_type=(ScenarioType.EXPENSE_REDUCTION),
        name="Food Reduction",
        description="Reduce food expenses.",
        parameters={
            "category": "Food",
            "reduction_percentage": 20,
            "horizon_months": 12,
        },
    )

    result = run_financial_scenario(
        request=request,
        snapshot=build_snapshot(),
    )

    assert result.scenario_type == ScenarioType.EXPENSE_REDUCTION
    assert result.projected_snapshot["total_expenses"] == 2880


def test_original_snapshot_is_not_mutated():
    snapshot = build_snapshot()

    run_expense_reduction_scenario(
        snapshot,
        {
            "category": "Food",
            "reduction_percentage": 20,
            "horizon_months": 12,
        },
    )

    assert snapshot["total_expenses"] == 3000
    assert snapshot["net_cash_flow"] == 2000
    assert snapshot["category_totals"]["Food"] == 600
