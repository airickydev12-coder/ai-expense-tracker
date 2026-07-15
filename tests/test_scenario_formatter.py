from src.financial.scenarios.comparison import (
    ComparisonDirection,
    MetricComparison,
)
from src.financial.scenarios.formatter import (
    format_metric_comparison,
    format_percentage,
    format_scenario_comparison_report,
    format_signed_currency,
)
from src.financial.scenarios.report import (
    ScenarioComparisonReport,
)


def build_comparison() -> MetricComparison:
    """Create a metric comparison for formatting tests."""
    return MetricComparison(
        metric="Net Worth",
        original_value=1000,
        projected_value=1500,
        change=500,
        percentage_change=50,
        direction=ComparisonDirection.IMPROVEMENT,
        higher_is_better=True,
    )


def build_report() -> ScenarioComparisonReport:
    """Create a comparison report for formatting tests."""
    comparison = build_comparison()

    return ScenarioComparisonReport(
        scenario_name="Income Increase",
        scenario_type="Income Increase",
        summary=("The scenario produces an overall improvement."),
        comparisons=[comparison],
        improvements=[comparison],
        declines=[],
        unchanged=[],
    )


def test_format_signed_currency():
    assert format_signed_currency(500) == "+$500.00"
    assert format_signed_currency(-500) == "-$500.00"
    assert format_signed_currency(0) == "$0.00"


def test_format_percentage():
    assert format_percentage(25) == "+25.00%"
    assert format_percentage(-25) == "-25.00%"
    assert format_percentage(0) == "0.00%"
    assert format_percentage(None) == "N/A"


def test_format_metric_comparison():
    output = format_metric_comparison(build_comparison())

    assert "Net Worth" in output
    assert "$1,000.00" in output
    assert "$1,500.00" in output
    assert "+$500.00" in output
    assert "+50.00%" in output
    assert "Improvement" in output


def test_format_scenario_comparison_report():
    output = format_scenario_comparison_report(build_report())

    assert "Scenario Comparison Report" in output
    assert "Income Increase" in output
    assert "Net Worth" in output
    assert "Improvements: 1" in output
    assert "Declines:     0" in output
    assert "Unchanged:    0" in output
