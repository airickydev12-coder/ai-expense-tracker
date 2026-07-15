from src.financial.history.analytics import (
    get_cash_flow_change,
    get_expense_change,
    get_health_score_change,
    get_income_change,
    get_net_worth_change,
)
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.trend_direction import (
    FinancialMomentum,
    TrendDirection,
)
from src.financial.history.trend_summary import (
    FinancialTrendSummary,
    MetricTrend,
)


CURRENCY_TREND_THRESHOLD = 25.0
HEALTH_SCORE_TREND_THRESHOLD = 2


def classify_financial_change(
    change: float,
    threshold: float = CURRENCY_TREND_THRESHOLD,
) -> TrendDirection:
    """
    Classify a financial change where an increase is beneficial.

    This classification is appropriate for metrics such as income,
    cash flow, and net worth.
    """
    if abs(change) < threshold:
        return TrendDirection.STABLE

    if change > 0:
        return TrendDirection.IMPROVING

    return TrendDirection.DECLINING


def classify_expense_change(
    change: float,
    threshold: float = CURRENCY_TREND_THRESHOLD,
) -> TrendDirection:
    """
    Classify an expense change.

    Lower expenses are considered improving, while higher expenses
    are considered declining.
    """
    if abs(change) < threshold:
        return TrendDirection.STABLE

    if change < 0:
        return TrendDirection.IMPROVING

    return TrendDirection.DECLINING


def classify_health_score_change(
    change: int,
    threshold: int = HEALTH_SCORE_TREND_THRESHOLD,
) -> TrendDirection:
    """Classify a change in financial health score."""
    if abs(change) < threshold:
        return TrendDirection.STABLE

    if change > 0:
        return TrendDirection.IMPROVING

    return TrendDirection.DECLINING


def calculate_overall_momentum(
    trends: list[MetricTrend],
) -> FinancialMomentum:
    """Calculate overall momentum from individual metric trends."""
    improving_count = sum(
        1
        for trend in trends
        if trend.direction == TrendDirection.IMPROVING
    )

    declining_count = sum(
        1
        for trend in trends
        if trend.direction == TrendDirection.DECLINING
    )

    if improving_count > declining_count:
        return FinancialMomentum.POSITIVE

    if declining_count > improving_count:
        return FinancialMomentum.NEGATIVE

    return FinancialMomentum.STABLE


def build_insufficient_data_summary() -> FinancialTrendSummary:
    """Return a trend summary when fewer than two snapshots exist."""
    unavailable_trend = MetricTrend(
        direction=TrendDirection.INSUFFICIENT_DATA,
        change=0.0,
    )

    return FinancialTrendSummary(
        net_worth=unavailable_trend,
        cash_flow=unavailable_trend,
        income=unavailable_trend,
        expenses=unavailable_trend,
        health_score=unavailable_trend,
        overall_momentum=(
            FinancialMomentum.INSUFFICIENT_DATA
        ),
    )


def analyze_financial_trends(
    history: list[FinancialSnapshotRecord],
) -> FinancialTrendSummary:
    """Analyze changes across historical financial snapshots."""
    if len(history) < 2:
        return build_insufficient_data_summary()

    net_worth_change = get_net_worth_change(history)
    cash_flow_change = get_cash_flow_change(history)
    income_change = get_income_change(history)
    expense_change = get_expense_change(history)
    health_score_change = get_health_score_change(history)

    net_worth_trend = MetricTrend(
        direction=classify_financial_change(
            net_worth_change
        ),
        change=net_worth_change,
    )

    cash_flow_trend = MetricTrend(
        direction=classify_financial_change(
            cash_flow_change
        ),
        change=cash_flow_change,
    )

    income_trend = MetricTrend(
        direction=classify_financial_change(
            income_change
        ),
        change=income_change,
    )

    expense_trend = MetricTrend(
        direction=classify_expense_change(
            expense_change
        ),
        change=expense_change,
    )

    health_score_trend = MetricTrend(
        direction=classify_health_score_change(
            health_score_change
        ),
        change=float(health_score_change),
    )

    overall_momentum = calculate_overall_momentum(
        [
            net_worth_trend,
            cash_flow_trend,
            income_trend,
            expense_trend,
            health_score_trend,
        ]
    )

    return FinancialTrendSummary(
        net_worth=net_worth_trend,
        cash_flow=cash_flow_trend,
        income=income_trend,
        expenses=expense_trend,
        health_score=health_score_trend,
        overall_momentum=overall_momentum,
    )