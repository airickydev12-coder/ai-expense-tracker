import pytest

from src.financial.scenarios.models import (
    ScenarioAssumption,
    ScenarioImpact,
    ScenarioRequest,
    ScenarioResult,
    ScenarioType,
)


def build_snapshot() -> dict:
    """Create a financial snapshot for scenario tests."""
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


def test_scenario_assumption():
    assumption = ScenarioAssumption(
        name="Reduction Percentage",
        value=20,
        description="Reduce dining by 20 percent.",
    )

    assert assumption.name == "Reduction Percentage"
    assert assumption.value == 20
    assert assumption.to_dict() == {
        "name": "Reduction Percentage",
        "value": 20,
        "description": ("Reduce dining by 20 percent."),
    }


def test_scenario_assumption_rejects_empty_name():
    with pytest.raises(
        ValueError,
        match="name cannot be empty",
    ):
        ScenarioAssumption(
            name=" ",
            value=20,
        )


def test_scenario_impact_create():
    impact = ScenarioImpact.create(
        metric="Net Cash Flow",
        original_value=2000,
        projected_value=2300,
    )

    assert impact.metric == "Net Cash Flow"
    assert impact.original_value == 2000
    assert impact.projected_value == 2300
    assert impact.change == 300


def test_scenario_impact_rejects_empty_metric():
    with pytest.raises(
        ValueError,
        match="metric cannot be empty",
    ):
        ScenarioImpact.create(
            metric=" ",
            original_value=0,
            projected_value=100,
        )


def test_scenario_request_copies_parameters():
    parameters = {
        "percentage": 10,
    }

    request = ScenarioRequest(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Income Increase",
        description="Model a raise.",
        parameters=parameters,
    )

    parameters["percentage"] = 50

    assert request.parameters["percentage"] == 10


def test_scenario_request_rejects_empty_name():
    with pytest.raises(
        ValueError,
        match="name cannot be empty",
    ):
        ScenarioRequest(
            scenario_type=(ScenarioType.INCOME_INCREASE),
            name=" ",
            description="",
            parameters={},
        )


def test_scenario_result():
    original_snapshot = build_snapshot()

    projected_snapshot = {
        **original_snapshot,
        "net_cash_flow": 2300,
    }

    result = ScenarioResult(
        scenario_type=(ScenarioType.EXPENSE_REDUCTION),
        name="Dining Reduction",
        description="Reduce dining costs.",
        assumptions=[
            ScenarioAssumption(
                name="Reduction Percentage",
                value=20,
            )
        ],
        original_snapshot=original_snapshot,
        projected_snapshot=projected_snapshot,
        impacts=[
            ScenarioImpact.create(
                metric="Net Cash Flow",
                original_value=2000,
                projected_value=2300,
            )
        ],
        benefits=[
            "More monthly cash flow.",
        ],
        risks=[
            "The target may be difficult.",
        ],
        recommendations=[
            "Track dining expenses weekly.",
        ],
    )

    impact = result.get_impact("net cash flow")

    assert impact is not None
    assert impact.change == 300
    assert result.benefits == ["More monthly cash flow."]
    assert result.to_dict()["scenario_type"] == "EXPENSE_REDUCTION"


def test_scenario_result_returns_none_for_missing_impact():
    result = ScenarioResult(
        scenario_type=(ScenarioType.ADDITIONAL_SAVINGS),
        name="Additional Savings",
        description="",
        assumptions=[],
        original_snapshot=build_snapshot(),
        projected_snapshot=build_snapshot(),
        impacts=[],
    )

    assert result.get_impact("Missing") is None


def test_scenario_result_copies_snapshots():
    original_snapshot = build_snapshot()
    projected_snapshot = build_snapshot()

    result = ScenarioResult(
        scenario_type=(ScenarioType.ADDITIONAL_SAVINGS),
        name="Additional Savings",
        description="",
        assumptions=[],
        original_snapshot=original_snapshot,
        projected_snapshot=projected_snapshot,
        impacts=[],
    )

    original_snapshot["net_worth"] = 999999
    projected_snapshot["net_worth"] = 999999

    assert result.original_snapshot["net_worth"] == 500
    assert result.projected_snapshot["net_worth"] == 500
