from src.financial.scenarios.comparison import (
    MetricComparison,
)
from src.financial.scenarios.report import (
    ScenarioComparisonReport,
)


def format_signed_currency(
    value: float,
) -> str:
    """Format a signed currency value."""
    if value > 0:
        return f"+${value:,.2f}"

    if value < 0:
        return f"-${abs(value):,.2f}"

    return "$0.00"


def format_percentage(
    value: float | None,
) -> str:
    """Format an optional percentage change."""
    if value is None:
        return "N/A"

    if value > 0:
        return f"+{value:.2f}%"

    return f"{value:.2f}%"


def format_metric_comparison(
    comparison: MetricComparison,
) -> str:
    """Format one comparison for text-based output."""
    return "\n".join(
        [
            comparison.metric,
            ("  Current:    " f"${comparison.original_value:,.2f}"),
            ("  Projected:  " f"${comparison.projected_value:,.2f}"),
            ("  Change:     " f"{format_signed_currency(comparison.change)}"),
            (
                "  Percentage: "
                f"{format_percentage(
                    comparison.percentage_change
                )}"
            ),
            ("  Direction:  " f"{comparison.direction.value}"),
        ]
    )


def format_scenario_comparison_report(
    report: ScenarioComparisonReport,
) -> str:
    """Format a complete scenario comparison report."""
    lines = [
        "========================================",
        "       Scenario Comparison Report",
        "========================================",
        f"Scenario: {report.scenario_name}",
        f"Type:     {report.scenario_type}",
        "",
        report.summary,
        "",
        "Metric Comparisons",
        "----------------------------------------",
    ]

    if not report.comparisons:
        lines.append("No comparable financial metrics were found.")
    else:
        for comparison in report.comparisons:
            lines.append(format_metric_comparison(comparison))
            lines.append("")

    lines.extend(
        [
            "Summary Counts",
            "----------------------------------------",
            ("Improvements: " f"{len(report.improvements)}"),
            ("Declines:     " f"{len(report.declines)}"),
            ("Unchanged:    " f"{len(report.unchanged)}"),
            "========================================",
        ]
    )

    return "\n".join(lines)
