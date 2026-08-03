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

_history: dict[int, list[FinancialSnapshotRecord]] = {}


def _ensure_loaded(user_id: int, db_path: Path = DB_PATH) -> None:
    """Lazily load a user's history into the cache on first access."""
    if user_id not in _history:
        _history[user_id] = load_history_from_file(user_id, db_path)


def load_history(
    user_id: int,
    file_path: Path = DB_PATH,
) -> None:
    """Load a user's historical snapshots into application memory."""
    _history[user_id] = load_history_from_file(user_id, file_path)


def save_history(user_id: int, file_path: Path = DB_PATH) -> None:
    """Save all of a user's historical snapshots."""
    save_history_to_file(
        _history[user_id],
        user_id,
        file_path,
    )


def get_history(user_id: int, db_path: Path = DB_PATH) -> list[FinancialSnapshotRecord]:
    """Return a copy of all of a user's historical snapshots."""
    _ensure_loaded(user_id, db_path)
    return _history[user_id].copy()


def get_latest_snapshot(
    user_id: int, db_path: Path = DB_PATH
) -> FinancialSnapshotRecord | None:
    """Return a user's most recent historical snapshot."""
    _ensure_loaded(user_id, db_path)

    if not _history[user_id]:
        return None

    return max(
        _history[user_id],
        key=lambda record: record.timestamp,
    )


def record_snapshot(
    user_id: int,
    snapshot: dict,
    file_path: Path = DB_PATH,
    timestamp: datetime | None = None,
) -> FinancialSnapshotRecord:
    """Create and persist a historical snapshot record for this user."""
    _ensure_loaded(user_id, file_path)

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
        category_totals={
            category: to_money(amount)
            for category, amount in snapshot.get("category_totals", {}).items()
        },
    )

    _history[user_id].append(record)
    save_history(user_id, file_path)

    logger.info(
        "Recorded financial snapshot at %s (health score %d) for user %d",
        record.timestamp.isoformat(),
        record.health_score,
        user_id,
    )

    return record


def clear_history(user_id: int | None = None) -> None:
    """Clear historical snapshots from application memory.

    Clears every cached user's history when `user_id` is omitted (test
    convenience, matching the old module-level-list behavior), or just one
    user's history when given.
    """
    if user_id is None:
        _history.clear()
        return

    _history[user_id] = []
