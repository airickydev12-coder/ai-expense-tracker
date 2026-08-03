from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.core.money import ZERO
from src.financial.history.models import FinancialSnapshotRecord


def filter_history_within_days(
    history: list[FinancialSnapshotRecord],
    days: int,
    *,
    now: datetime | None = None,
) -> list[FinancialSnapshotRecord]:
    """Return snapshots with timestamp >= now - days, ordered oldest to newest."""
    reference = now if now is not None else datetime.now(timezone.utc)
    cutoff = reference - timedelta(days=days)

    return _sort_history(
        [record for record in history if record.timestamp >= cutoff]
    )


def _sort_history(
    history: list[FinancialSnapshotRecord],
) -> list[FinancialSnapshotRecord]:
    """Return snapshots ordered from oldest to newest."""
    return sorted(
        history,
        key=lambda record: record.timestamp,
    )


def get_net_worth_change(
    history: list[FinancialSnapshotRecord],
) -> Decimal:
    """Return net-worth change from oldest to newest snapshot."""
    if len(history) < 2:
        return ZERO

    ordered_history = _sort_history(history)

    return ordered_history[-1].net_worth - ordered_history[0].net_worth


def get_cash_flow_change(
    history: list[FinancialSnapshotRecord],
) -> Decimal:
    """Return cash-flow change from oldest to newest snapshot."""
    if len(history) < 2:
        return ZERO

    ordered_history = _sort_history(history)

    return ordered_history[-1].net_cash_flow - ordered_history[0].net_cash_flow


def get_health_score_change(
    history: list[FinancialSnapshotRecord],
) -> int:
    """Return health-score change from oldest to newest snapshot."""
    if len(history) < 2:
        return 0

    ordered_history = _sort_history(history)

    return ordered_history[-1].health_score - ordered_history[0].health_score


def get_income_change(
    history: list[FinancialSnapshotRecord],
) -> Decimal:
    """Return income change from oldest to newest snapshot."""
    if len(history) < 2:
        return ZERO

    ordered_history = _sort_history(history)

    return ordered_history[-1].total_income - ordered_history[0].total_income


def get_expense_change(
    history: list[FinancialSnapshotRecord],
) -> Decimal:
    """Return expense change from oldest to newest snapshot."""
    if len(history) < 2:
        return ZERO

    ordered_history = _sort_history(history)

    return ordered_history[-1].total_expenses - ordered_history[0].total_expenses


def get_category_totals_change(
    history: list[FinancialSnapshotRecord],
) -> dict[str, Decimal]:
    """Return per-category spending change from oldest to newest snapshot."""
    if len(history) < 2:
        return {}

    ordered_history = _sort_history(history)
    oldest = ordered_history[0].category_totals
    newest = ordered_history[-1].category_totals

    categories = set(oldest) | set(newest)

    return {
        category: newest.get(category, ZERO) - oldest.get(category, ZERO)
        for category in categories
    }
