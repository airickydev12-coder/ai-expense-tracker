from decimal import Decimal
from pathlib import Path

from src.core.config import DB_PATH
from src.core.logging import get_logger
from src.financial.events.bus import event_bus
from src.financial.events.event_types import FinancialEvent
from src.financial.income.models import Income
from src.financial.income.repository import (
    load_income_from_file,
    save_income_to_file,
)

logger = get_logger(__name__)

income_entries: dict[int, list[Income]] = {}


def _ensure_loaded(user_id: int, db_path: Path = DB_PATH) -> None:
    """Lazily load a user's income entries into the cache on first access."""
    if user_id not in income_entries:
        income_entries[user_id] = load_income_from_file(user_id, db_path)


def load_income(user_id: int, db_path: Path = DB_PATH) -> None:
    """Force-reload a user's income entries from the repository."""
    income_entries[user_id] = load_income_from_file(user_id, db_path)


def save_income(user_id: int, db_path: Path = DB_PATH) -> None:
    """Save a user's income entries using the repository."""
    save_income_to_file(income_entries[user_id], user_id, db_path)


def get_income_entries(user_id: int, db_path: Path = DB_PATH) -> list[Income]:
    """Return a copy of all of this user's income entries."""
    _ensure_loaded(user_id, db_path)
    return income_entries[user_id].copy()


def get_income_by_id(
    user_id: int,
    income_id: int,
    db_path: Path = DB_PATH,
) -> Income | None:
    """Return one of this user's income entries by ID."""
    _ensure_loaded(user_id, db_path)

    for income in income_entries[user_id]:
        if income.id == income_id:
            return income

    return None


def get_next_income_id(user_id: int) -> int:
    """Return the next available income ID for this user."""
    user_income_entries = income_entries.get(user_id, [])
    if not user_income_entries:
        return 1

    return max(income.id for income in user_income_entries) + 1


def add_income(
    user_id: int,
    source: str,
    amount: Decimal,
    db_path: Path = DB_PATH,
) -> Income:
    """Create and add a new income entry for this user."""
    _ensure_loaded(user_id, db_path)

    income = Income(
        id=get_next_income_id(user_id),
        source=source,
        amount=amount,
    )

    income_entries[user_id].append(income)
    save_income(user_id, db_path)
    event_bus.publish(FinancialEvent.INCOME_ADDED, income)

    logger.info(
        "Added income %d (%s) for user %d",
        income.id,
        income.source,
        user_id,
    )

    return income


def update_income(
    user_id: int,
    income_id: int,
    source: str | None = None,
    amount: Decimal | None = None,
    db_path: Path = DB_PATH,
) -> Income | None:
    """Update one of this user's existing income entries by ID."""
    _ensure_loaded(user_id, db_path)

    income = get_income_by_id(user_id, income_id, db_path)

    if income is None:
        return None

    updated_income = Income(
        id=income.id,
        source=(source.strip() if source is not None else income.source),
        amount=(amount if amount is not None else income.amount),
    )

    income_index = income_entries[user_id].index(income)
    income_entries[user_id][income_index] = updated_income

    save_income(user_id, db_path)

    logger.info(
        "Updated income %d for user %d",
        income_id,
        user_id,
    )

    return updated_income


def delete_income(user_id: int, income_id: int, db_path: Path = DB_PATH) -> Income | None:
    """Delete one of this user's income entries by ID."""
    _ensure_loaded(user_id, db_path)

    for index, income in enumerate(income_entries[user_id]):
        if income.id == income_id:
            deleted_income = income_entries[user_id].pop(index)
            save_income(user_id, db_path)
            logger.info(
                "Deleted income %d for user %d",
                income_id,
                user_id,
            )
            return deleted_income

    return None
