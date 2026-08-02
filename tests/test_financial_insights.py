import pytest

from src.financial.coach.insights import (
    FinancialCoachInsight,
    InsightSeverity,
    build_health_score_insights,
    calculate_debt_to_income_ratio,
    calculate_emergency_fund_months,
    calculate_savings_rate,
    find_top_spending_category,
    generate_financial_coach_insights,
)
from src.financial.recommendations.category import RecommendationCategory


def build_snapshot() -> dict:
    """Create a healthy snapshot for insight tests."""
    return {
        "total_income": 5000,
        "total_expenses": 3000,
        "net_cash_flow": 2000,
        "total_account_balance": 9000,
        "total_goal_progress": 2500,
        "total_debt": 12000,
        "net_worth": -500,
        "health_score": 68,
        "health_status": "Fair",
        "category_totals": {
            "Housing": 1500,
            "Food": 600,
            "Transportation": 400,
        },
    }


def test_financial_coach_insight():
    insight = FinancialCoachInsight(
        key="cash_flow:test",
        title="Positive Cash Flow",
        message="Cash flow is positive.",
        category=RecommendationCategory.CASH_FLOW,
        severity=InsightSeverity.POSITIVE,
        metric="Net Cash Flow",
        current_value=1000,
        benchmark_value=0,
        action="Save part of the surplus.",
    )

    assert insight.title == "Positive Cash Flow"
    assert insight.to_dict()["severity"] == "Positive"


def test_insight_rejects_empty_key():
    with pytest.raises(
        ValueError,
        match="key cannot be empty",
    ):
        FinancialCoachInsight(
            key=" ",
            title="Title",
            message="Message",
            category=RecommendationCategory.CASH_FLOW,
            severity=InsightSeverity.INFORMATIONAL,
        )


def test_calculate_savings_rate():
    assert calculate_savings_rate(build_snapshot()) == pytest.approx(40)


def test_savings_rate_returns_none_without_income():
    snapshot = build_snapshot()
    snapshot["total_income"] = 0

    assert calculate_savings_rate(snapshot) is None


def test_calculate_debt_to_income_ratio():
    ratio = calculate_debt_to_income_ratio(build_snapshot())

    assert ratio == pytest.approx(20)


def test_calculate_emergency_fund_months():
    coverage = calculate_emergency_fund_months(build_snapshot())

    assert coverage == pytest.approx(3)


def test_find_top_spending_category():
    assert find_top_spending_category(build_snapshot()) == (
        "Housing",
        1500,
    )


def test_generate_financial_coach_insights():
    insights = generate_financial_coach_insights(build_snapshot())

    keys = {insight.key for insight in insights}

    assert "cash_flow:positive" in keys
    assert "savings:rate" in keys
    assert "savings:emergency_fund" in keys
    assert "debt:balance" in keys
    assert "debt:income_ratio" in keys
    assert "net_worth:negative" in keys
    assert "financial_health:score" in keys


def test_critical_insights_are_prioritized():
    snapshot = build_snapshot()
    snapshot["net_cash_flow"] = -500
    snapshot["total_account_balance"] = 500

    insights = generate_financial_coach_insights(snapshot)

    assert insights[0].severity == InsightSeverity.CRITICAL


def test_no_debt_produces_positive_insight():
    snapshot = build_snapshot()
    snapshot["total_debt"] = 0

    insights = generate_financial_coach_insights(snapshot)

    debt_insight = next(insight for insight in insights if insight.key == "debt:none")

    assert debt_insight.severity == InsightSeverity.POSITIVE


def test_spending_concentration_warning():
    snapshot = build_snapshot()
    snapshot["total_expenses"] = 2000
    snapshot["category_totals"] = {
        "Housing": 1500,
        "Food": 500,
    }

    insights = generate_financial_coach_insights(snapshot)

    spending_insight = next(
        insight for insight in insights if insight.category == RecommendationCategory.EXPENSES
    )

    assert spending_insight.severity == InsightSeverity.WARNING


@pytest.mark.parametrize(
    "health_score,expected_severity",
    [
        (0, InsightSeverity.CRITICAL),
        (49, InsightSeverity.CRITICAL),
        (50, InsightSeverity.WARNING),
        (69, InsightSeverity.WARNING),
        (70, InsightSeverity.INFORMATIONAL),
        (84, InsightSeverity.INFORMATIONAL),
        (85, InsightSeverity.POSITIVE),
        (100, InsightSeverity.POSITIVE),
    ],
)
def test_health_score_insight_matches_canonical_thresholds(
    health_score,
    expected_severity,
):
    """
    Severity boundaries must match health_status.py's canonical
    30/50/70/85 grid (Critical/Needs Attention collapsed into one
    CRITICAL severity below 50), not an independently invented scale.
    """
    snapshot = build_snapshot()
    snapshot["health_score"] = health_score

    insight = build_health_score_insights(snapshot)[0]

    assert insight.severity == expected_severity
