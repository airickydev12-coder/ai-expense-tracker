from src.financial.scenarios.comparison import (
    ComparisonDirection,
)
from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.report import (
    build_report_summary,
    build_scenario_comparison_report,
)


def build_result() -> ScenarioResult:
    """Create a scenario result for report tests."""
    original = {
        "total_income": 5000,
        "total_expenses": 3000,
        "net_cash_flow": 2000,
        "total_account_balance": 8000,
        "total_goal_progress": 2500,
        "total_debt": 10000,
        "net_worth": 500,
        "health_score": 70,
    }

    projected = {
        **original,
        "total_expenses": 2800,
        "net_cash_flow": 2200,
        "total_account_balance": 10400,
        "net_worth": 2900,
    }

    return ScenarioResult(
        scenario_type=(ScenarioType.EXPENSE_REDUCTION),
        name="Food Expense Reduction",
        description="Reduce food spending.",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot=projected,
        impacts=[],
    )


def test_build_scenario_comparison_report():
    report = build_scenario_comparison_report(build_result())

    assert report.scenario_name == ("Food Expense Reduction")
    assert report.scenario_type == ("Expense Reduction")
    assert len(report.comparisons) == 8
    assert len(report.improvements) == 4
    assert len(report.declines) == 0
    assert len(report.unchanged) == 4
    assert "overall improvement" in report.summary


def test_report_get_comparison():
    report = build_scenario_comparison_report(build_result())

    comparison = report.get_comparison("net worth")

    assert comparison is not None
    assert comparison.change == 2400
    assert comparison.direction == ComparisonDirection.IMPROVEMENT


def test_report_returns_none_for_unknown_metric():
    report = build_scenario_comparison_report(build_result())

    assert report.get_comparison("Unknown") is None


def test_report_serialization():
    report = build_scenario_comparison_report(build_result())

    data = report.to_dict()

    assert data["scenario_name"] == ("Food Expense Reduction")
    assert len(data["comparisons"]) == 8
    assert len(data["improvements"]) == 4


def test_build_summary_for_decline():
    summary = build_report_summary(
        improvement_count=1,
        decline_count=3,
        unchanged_count=2,
    )

    assert "overall decline" in summary


def test_build_summary_for_balanced_result():
    summary = build_report_summary(
        improvement_count=2,
        decline_count=2,
        unchanged_count=1,
    )

    assert "balanced result" in summary


def test_build_summary_for_no_change():
    summary = build_report_summary(
        improvement_count=0,
        decline_count=0,
        unchanged_count=8,
    )

    assert "no measurable change" in summary
