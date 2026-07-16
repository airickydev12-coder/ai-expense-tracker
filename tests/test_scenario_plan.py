import pytest

from src.financial.scenarios.comparison import (
    ComparisonDirection,
)
from src.financial.scenarios.models import (
    ScenarioRequest,
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.plan import (
    ScenarioPlanResult,
    ScenarioPlanStep,
    build_cumulative_scenario_report,
)


def build_snapshot() -> dict:
    """Create a baseline snapshot."""
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


def build_request() -> ScenarioRequest:
    """Create a reusable scenario request."""
    return ScenarioRequest(
        scenario_type=ScenarioType.INCOME_INCREASE,
        name="Income Increase",
        description="Increase income.",
        parameters={
            "increase_percentage": 10,
        },
    )


def build_result() -> ScenarioResult:
    """Create a reusable scenario result."""
    original = build_snapshot()

    return ScenarioResult(
        scenario_type=ScenarioType.INCOME_INCREASE,
        name="Income Increase",
        description="Increase income.",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot={
            **original,
            "total_income": 5500,
            "net_cash_flow": 2500,
            "net_worth": 6500,
        },
        impacts=[],
    )


def test_scenario_plan_step():
    step = ScenarioPlanStep(
        order=1,
        request=build_request(),
        result=build_result(),
    )

    assert step.order == 1
    assert step.result.name == "Income Increase"
    assert step.to_dict()["order"] == 1


def test_scenario_plan_step_rejects_invalid_order():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        ScenarioPlanStep(
            order=0,
            request=build_request(),
            result=build_result(),
        )


def test_build_cumulative_scenario_report():
    original = build_snapshot()

    projected = {
        **original,
        "total_expenses": 2800,
        "net_cash_flow": 2200,
        "total_debt": 9000,
        "net_worth": 2000,
    }

    report = build_cumulative_scenario_report(
        original,
        projected,
    )

    assert len(report.comparisons) == 8
    assert len(report.improvements) == 4
    assert len(report.declines) == 0
    assert len(report.unchanged) == 4

    debt_comparison = report.get_comparison("Total Debt")

    assert debt_comparison is not None
    assert debt_comparison.change == -1000
    assert debt_comparison.direction == ComparisonDirection.IMPROVEMENT


def test_scenario_plan_result():
    original = build_snapshot()
    result = build_result()

    step = ScenarioPlanStep(
        order=1,
        request=build_request(),
        result=result,
    )

    report = build_cumulative_scenario_report(
        original,
        result.projected_snapshot,
    )

    plan = ScenarioPlanResult(
        name="Primary Plan",
        description="Combined financial plan.",
        original_snapshot=original,
        projected_snapshot=(result.projected_snapshot),
        steps=[step],
        cumulative_report=report,
        benefits=[
            "More income.",
            "More income.",
        ],
        risks=[],
        recommendations=[
            "Save additional income.",
        ],
    )

    assert plan.name == "Primary Plan"
    assert len(plan.steps) == 1
    assert plan.benefits == ["More income."]
    assert plan.get_step(1) == step
    assert plan.get_metric_change("Net Worth") == 6000


def test_scenario_plan_result_rejects_empty_name():
    report = build_cumulative_scenario_report(
        build_snapshot(),
        build_snapshot(),
    )

    with pytest.raises(
        ValueError,
        match="name cannot be empty",
    ):
        ScenarioPlanResult(
            name=" ",
            description="",
            original_snapshot=build_snapshot(),
            projected_snapshot=build_snapshot(),
            steps=[],
            cumulative_report=report,
        )


def test_scenario_plan_serialization():
    result = build_result()

    step = ScenarioPlanStep(
        order=1,
        request=build_request(),
        result=result,
    )

    report = build_cumulative_scenario_report(
        build_snapshot(),
        result.projected_snapshot,
    )

    plan = ScenarioPlanResult(
        name="Primary Plan",
        description="",
        original_snapshot=build_snapshot(),
        projected_snapshot=result.projected_snapshot,
        steps=[step],
        cumulative_report=report,
    )

    data = plan.to_dict()

    assert data["name"] == "Primary Plan"
    assert len(data["steps"]) == 1
    assert "cumulative_report" in data
