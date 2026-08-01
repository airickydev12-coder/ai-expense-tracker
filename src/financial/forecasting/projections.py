from collections.abc import Callable
from decimal import Decimal

from src.core.money import ZERO
from src.financial.forecasting.models import MetricProjection
from src.financial.history.models import FinancialSnapshotRecord


MetricGetter = Callable[[FinancialSnapshotRecord], Decimal]


def validate_forecast_horizon(
    horizon_days: int,
) -> None:
    """Validate a forecast horizon."""
    if horizon_days <= 0:
        raise ValueError(
            "Forecast horizon must be greater than zero."
        )


def sort_history(
    history: list[FinancialSnapshotRecord],
) -> list[FinancialSnapshotRecord]:
    """Return history ordered from oldest to newest."""
    return sorted(
        history,
        key=lambda record: record.timestamp,
    )


def calculate_elapsed_days(
    first_record: FinancialSnapshotRecord,
    last_record: FinancialSnapshotRecord,
) -> float:
    """Return elapsed time between two records in fractional days."""
    elapsed_seconds = (
        last_record.timestamp
        - first_record.timestamp
    ).total_seconds()

    return elapsed_seconds / 86400


def calculate_daily_change(
    history: list[FinancialSnapshotRecord],
    value_getter: MetricGetter,
) -> Decimal:
    """Calculate average daily change for one metric."""
    if len(history) < 2:
        return ZERO

    ordered_history = sort_history(history)
    first_record = ordered_history[0]
    last_record = ordered_history[-1]

    elapsed_days = calculate_elapsed_days(
        first_record,
        last_record,
    )

    if elapsed_days <= 0:
        return ZERO

    first_value = value_getter(first_record)
    last_value = value_getter(last_record)

    return (
        last_value - first_value
    ) / Decimal(str(elapsed_days))


def project_metric(
    *,
    metric: str,
    history: list[FinancialSnapshotRecord],
    value_getter: MetricGetter,
    horizon_days: int,
    minimum_value: Decimal | None = None,
    maximum_value: Decimal | None = None,
) -> MetricProjection:
    """Project one financial metric using its historical daily change."""
    validate_forecast_horizon(horizon_days)

    if not history:
        raise ValueError(
            "At least one historical snapshot is required."
        )

    ordered_history = sort_history(history)
    current_value = value_getter(
        ordered_history[-1]
    )

    daily_change = calculate_daily_change(
        ordered_history,
        value_getter,
    )

    projected_value = (
        current_value
        + daily_change * horizon_days
    )

    if minimum_value is not None:
        projected_value = max(
            projected_value,
            minimum_value,
        )

    if maximum_value is not None:
        projected_value = min(
            projected_value,
            maximum_value,
        )

    projected_change = (
        projected_value - current_value
    )

    return MetricProjection(
        metric=metric,
        current_value=current_value,
        projected_value=projected_value,
        projected_change=projected_change,
        daily_change=daily_change,
        horizon_days=horizon_days,
    )


def project_net_worth(
    history: list[FinancialSnapshotRecord],
    horizon_days: int,
) -> MetricProjection:
    """Project net worth."""
    return project_metric(
        metric="Net Worth",
        history=history,
        value_getter=lambda record: record.net_worth,
        horizon_days=horizon_days,
    )


def project_cash_flow(
    history: list[FinancialSnapshotRecord],
    horizon_days: int,
) -> MetricProjection:
    """Project net cash flow."""
    return project_metric(
        metric="Cash Flow",
        history=history,
        value_getter=lambda record: record.net_cash_flow,
        horizon_days=horizon_days,
    )


def project_account_balance(
    history: list[FinancialSnapshotRecord],
    horizon_days: int,
) -> MetricProjection:
    """Project total account balance."""
    return project_metric(
        metric="Account Balance",
        history=history,
        value_getter=(
            lambda record: record.total_account_balance
        ),
        horizon_days=horizon_days,
        minimum_value=ZERO,
    )


def project_goal_progress(
    history: list[FinancialSnapshotRecord],
    horizon_days: int,
) -> MetricProjection:
    """Project total financial-goal progress."""
    return project_metric(
        metric="Goal Progress",
        history=history,
        value_getter=(
            lambda record: record.total_goal_progress
        ),
        horizon_days=horizon_days,
        minimum_value=ZERO,
    )


def project_total_debt(
    history: list[FinancialSnapshotRecord],
    horizon_days: int,
) -> MetricProjection:
    """Project total outstanding debt."""
    return project_metric(
        metric="Total Debt",
        history=history,
        value_getter=lambda record: record.total_debt,
        horizon_days=horizon_days,
        minimum_value=ZERO,
    )


def project_health_score(
    history: list[FinancialSnapshotRecord],
    horizon_days: int,
) -> MetricProjection:
    """Project financial health score."""
    return project_metric(
        metric="Health Score",
        history=history,
        value_getter=(
            lambda record: Decimal(record.health_score)
        ),
        horizon_days=horizon_days,
        minimum_value=ZERO,
        maximum_value=Decimal("100"),
    )