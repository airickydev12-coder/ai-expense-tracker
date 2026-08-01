from datetime import datetime, timezone
from pathlib import Path

from src.core.config import DB_PATH
from src.core.logging import get_logger
from src.core.money import to_money
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.repository import (
    load_history_from_file,
    save_history_to_file,
)

logger = get_logger(__name__)

_history: list[FinancialSnapshotRecord] = []
_loaded_file_path: Path = DB_PATH


def load_history(
    file_path: Path = DB_PATH,
) -> None:
    """Load historical snapshots into application memory."""
    global _loaded_file_path

    _history.clear()
    _history.extend(load_history_from_file(file_path))

    _loaded_file_path = file_path


def save_history(
    file_path: Path | None = None,
) -> None:
    """Save all historical snapshots."""
    target_path = file_path if file_path is not None else _loaded_file_path

    save_history_to_file(
        _history,
        target_path,
    )


def get_history() -> list[FinancialSnapshotRecord]:
    """Return a copy of all historical snapshots."""
    return _history.copy()


def get_latest_snapshot() -> FinancialSnapshotRecord | None:
    """Return the most recent historical snapshot."""
    if not _history:
        return None

    return max(
        _history,
        key=lambda record: record.timestamp,
    )


def record_snapshot(
    snapshot: dict,
    file_path: Path | None = None,
    timestamp: datetime | None = None,
) -> FinancialSnapshotRecord:
    """Create and persist a historical snapshot record."""
    record = FinancialSnapshotRecord(
        timestamp=(timestamp if timestamp is not None else datetime.now(timezone.utc)),
        total_income=to_money(snapshot["total_income"]),
        total_expenses=to_money(snapshot["total_expenses"]),
        net_cash_flow=to_money(snapshot["net_cash_flow"]),
        total_account_balance=to_money(snapshot["total_account_balance"]),
        total_goal_progress=to_money(snapshot["total_goal_progress"]),
        total_debt=to_money(snapshot["total_debt"]),
        net_worth=to_money(snapshot["net_worth"]),
        health_score=int(snapshot["health_score"]),
        health_status=str(snapshot["health_status"]),
    )

    _history.append(record)
    save_history(file_path)

    logger.info(
        "Recorded financial snapshot at %s (health score %d)",
        record.timestamp.isoformat(),
        record.health_score,
    )

    return record


def clear_history() -> None:
    """Clear historical snapshots from application memory."""
    _history.clear()
