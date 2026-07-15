import pytest

from src.financial.scenarios.comparison import (
    ComparisonDirection,
    calculate_percentage_change,
    classify_comparison_direction,
    compare_metric,
    compare_snapshots,
)


def test_calculate_percentage_change():
    assert calculate_percentage_change(
        100,
        125,
    ) == pytest.approx(25)


def test_percentage_change_uses_absolute_original():
    assert calculate_percentage_change(
        -100,
        -50,
    ) == pytest.approx(50)


def test_percentage_change_returns_none_for_zero_original():
    assert (
        calculate_percentage_change(
            0,
            100,
        )
        is None
    )


def test_classify_higher_is_better_improvement():
    assert (
        classify_comparison_direction(
            change=100,
            higher_is_better=True,
        )
        == ComparisonDirection.IMPROVEMENT
    )


def test_classify_higher_is_better_decline():
    assert (
        classify_comparison_direction(
            change=-100,
            higher_is_better=True,
        )
        == ComparisonDirection.DECLINE
    )


def test_classify_lower_is_better_improvement():
    assert (
        classify_comparison_direction(
            change=-100,
            higher_is_better=False,
        )
        == ComparisonDirection.IMPROVEMENT
    )


def test_classify_lower_is_better_decline():
    assert (
        classify_comparison_direction(
            change=100,
            higher_is_better=False,
        )
        == ComparisonDirection.DECLINE
    )


def test_classify_unchanged_within_tolerance():
    assert (
        classify_comparison_direction(
            change=0.001,
            higher_is_better=True,
        )
        == ComparisonDirection.UNCHANGED
    )


def test_compare_metric():
    comparison = compare_metric(
        metric="Net Worth",
        original_value=1000,
        projected_value=1500,
        higher_is_better=True,
    )

    assert comparison.metric == "Net Worth"
    assert comparison.change == 500
    assert comparison.percentage_change == pytest.approx(50)
    assert comparison.direction == ComparisonDirection.IMPROVEMENT


def test_compare_snapshots():
    original = {
        "total_income": 5000,
        "total_expenses": 3000,
        "net_cash_flow": 2000,
        "total_debt": 10000,
        "net_worth": 500,
        "health_score": 70,
    }

    projected = {
        "total_income": 5500,
        "total_expenses": 2800,
        "net_cash_flow": 2700,
        "total_debt": 9000,
        "net_worth": 2000,
        "health_score": 75,
    }

    comparisons = compare_snapshots(
        original,
        projected,
    )

    by_metric = {comparison.metric: comparison for comparison in comparisons}

    assert by_metric["Total Income"].direction == ComparisonDirection.IMPROVEMENT
    assert by_metric["Total Expenses"].direction == ComparisonDirection.IMPROVEMENT
    assert by_metric["Total Debt"].direction == ComparisonDirection.IMPROVEMENT
    assert by_metric["Net Worth"].change == 1500


def test_compare_snapshots_skips_missing_fields():
    comparisons = compare_snapshots(
        {
            "net_worth": 1000,
        },
        {
            "net_worth": 1500,
        },
    )

    assert len(comparisons) == 1
    assert comparisons[0].metric == "Net Worth"


def test_comparison_rejects_empty_metric():
    with pytest.raises(
        ValueError,
        match="metric cannot be empty",
    ):
        compare_metric(
            metric=" ",
            original_value=0,
            projected_value=100,
            higher_is_better=True,
        )
