from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.trend_direction import (
    FinancialMomentum,
    TrendDirection,
)
from src.financial.history.trend_summary import MetricTrend
from src.financial.history.trends import (
    analyze_financial_trends,
    calculate_overall_momentum,
    classify_expense_change,
    classify_financial_change,
    classify_health_score_change,
)


def build_history(
    *,
    newer_income: Decimal = Decimal("5000"),
    newer_expenses: Decimal = Decimal("1800"),
    newer_cash_flow: Decimal = Decimal("3200"),
    newer_net_worth: Decimal = Decimal("3000"),
    newer_health_score: int = 80,
) -> list[FinancialSnapshotRecord]:
    """Create historical snapshots for trend tests."""
    now = datetime.now(timezone.utc)

    older = FinancialSnapshotRecord(
        timestamp=now - timedelta(days=30),
        total_income=Decimal("4000"),
        total_expenses=Decimal("2000"),
        net_cash_flow=Decimal("2000"),
        total_account_balance=Decimal("1500"),
        total_goal_progress=Decimal("1000"),
        total_debt=Decimal("2000"),
        net_worth=Decimal("500"),
        health_score=60,
        health_status="Fair",
    )

    newer = FinancialSnapshotRecord(
        timestamp=now,
        total_income=newer_income,
        total_expenses=newer_expenses,
        net_cash_flow=newer_cash_flow,
        total_account_balance=Decimal("2500"),
        total_goal_progress=Decimal("2000"),
        total_debt=Decimal("1500"),
        net_worth=newer_net_worth,
        health_score=newer_health_score,
        health_status="Good",
    )

    return [older, newer]


def test_classify_positive_financial_change():
    assert classify_financial_change(Decimal("100")) == TrendDirection.IMPROVING


def test_classify_negative_financial_change():
    assert classify_financial_change(Decimal("-100")) == TrendDirection.DECLINING


def test_classify_small_financial_change_as_stable():
    assert classify_financial_change(Decimal("24.99")) == TrendDirection.STABLE


def test_classify_exact_currency_threshold():
    assert classify_financial_change(Decimal("25")) == TrendDirection.IMPROVING

    assert classify_financial_change(Decimal("-25")) == TrendDirection.DECLINING


def test_classify_expense_decrease_as_improving():
    assert classify_expense_change(Decimal("-100")) == TrendDirection.IMPROVING


def test_classify_expense_increase_as_declining():
    assert classify_expense_change(Decimal("100")) == TrendDirection.DECLINING


def test_classify_small_expense_change_as_stable():
    assert classify_expense_change(Decimal("10")) == TrendDirection.STABLE


def test_classify_health_score_change():
    assert classify_health_score_change(2) == TrendDirection.IMPROVING

    assert classify_health_score_change(-2) == TrendDirection.DECLINING

    assert classify_health_score_change(1) == TrendDirection.STABLE


def test_calculate_positive_momentum():
    trends = [
        MetricTrend(
            TrendDirection.IMPROVING,
            Decimal("100"),
        ),
        MetricTrend(
            TrendDirection.IMPROVING,
            Decimal("200"),
        ),
        MetricTrend(
            TrendDirection.DECLINING,
            Decimal("-50"),
        ),
    ]

    assert calculate_overall_momentum(trends) == FinancialMomentum.POSITIVE


def test_calculate_negative_momentum():
    trends = [
        MetricTrend(
            TrendDirection.DECLINING,
            Decimal("-100"),
        ),
        MetricTrend(
            TrendDirection.DECLINING,
            Decimal("-200"),
        ),
        MetricTrend(
            TrendDirection.IMPROVING,
            Decimal("50"),
        ),
    ]

    assert calculate_overall_momentum(trends) == FinancialMomentum.NEGATIVE


def test_calculate_stable_momentum_when_tied():
    trends = [
        MetricTrend(
            TrendDirection.IMPROVING,
            Decimal("100"),
        ),
        MetricTrend(
            TrendDirection.DECLINING,
            Decimal("-100"),
        ),
        MetricTrend(
            TrendDirection.STABLE,
            Decimal("0"),
        ),
    ]

    assert calculate_overall_momentum(trends) == FinancialMomentum.STABLE


def test_analyze_financial_trends():
    summary = analyze_financial_trends(build_history())

    assert summary.net_worth.direction == TrendDirection.IMPROVING
    assert summary.cash_flow.direction == TrendDirection.IMPROVING
    assert summary.income.direction == TrendDirection.IMPROVING
    assert summary.expenses.direction == TrendDirection.IMPROVING
    assert summary.health_score.direction == TrendDirection.IMPROVING
    assert summary.overall_momentum == FinancialMomentum.POSITIVE


def test_analyze_declining_financial_trends():
    summary = analyze_financial_trends(
        build_history(
            newer_income=Decimal("3500"),
            newer_expenses=Decimal("2500"),
            newer_cash_flow=Decimal("1000"),
            newer_net_worth=Decimal("100"),
            newer_health_score=50,
        )
    )

    assert summary.net_worth.direction == TrendDirection.DECLINING
    assert summary.cash_flow.direction == TrendDirection.DECLINING
    assert summary.income.direction == TrendDirection.DECLINING
    assert summary.expenses.direction == TrendDirection.DECLINING
    assert summary.health_score.direction == TrendDirection.DECLINING
    assert summary.overall_momentum == FinancialMomentum.NEGATIVE


def test_analyze_financial_trends_with_insufficient_data():
    summary = analyze_financial_trends([])

    assert summary.net_worth.direction == TrendDirection.INSUFFICIENT_DATA
    assert summary.cash_flow.direction == TrendDirection.INSUFFICIENT_DATA
    assert summary.overall_momentum == FinancialMomentum.INSUFFICIENT_DATA


def test_trend_summary_serialization():
    summary = analyze_financial_trends(build_history())

    data = summary.to_dict()

    assert data["net_worth"]["direction"] == "Improving"
    assert data["net_worth"]["change"] == 2500
    assert data["expenses"]["direction"] == "Improving"
    assert data["overall_momentum"] == "Positive"
