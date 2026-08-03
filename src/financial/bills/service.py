from decimal import Decimal
from pathlib import Path

from src.core.config import DB_PATH
from src.core.logging import get_logger
from src.financial.bills.models import Bill
from src.financial.bills.repository import (
    load_bills_from_file,
    save_bills_to_file,
)

logger = get_logger(__name__)

bills: dict[int, list[Bill]] = {}


def _ensure_loaded(user_id: int, db_path: Path = DB_PATH) -> None:
    """Lazily load a user's bills into the cache on first access."""
    if user_id not in bills:
        bills[user_id] = load_bills_from_file(user_id, db_path)


def load_bills(user_id: int, db_path: Path = DB_PATH) -> None:
    """Force-reload a user's bills from the repository."""
    bills[user_id] = load_bills_from_file(user_id, db_path)


def save_bills(user_id: int, db_path: Path = DB_PATH) -> None:
    """Save a user's bills using the repository."""
    save_bills_to_file(bills[user_id], user_id, db_path)


def get_bills(user_id: int, db_path: Path = DB_PATH) -> list[Bill]:
    """Return a copy of all of this user's bills."""
    _ensure_loaded(user_id, db_path)
    return bills[user_id].copy()


def get_bill_by_id(
    user_id: int,
    bill_id: int,
    db_path: Path = DB_PATH,
) -> Bill | None:
    """Return one of this user's bills by ID."""
    _ensure_loaded(user_id, db_path)

    for bill in bills[user_id]:
        if bill.id == bill_id:
            return bill

    return None


def get_next_bill_id(user_id: int) -> int:
    """Return the next available bill ID for this user."""
    user_bills = bills.get(user_id, [])
    if not user_bills:
        return 1

    return max(bill.id for bill in user_bills) + 1


def add_bill(
    user_id: int,
    name: str,
    amount: Decimal,
    due_day: int,
    is_paid: bool = False,
    db_path: Path = DB_PATH,
) -> Bill:
    """Create and save a bill for this user."""
    _ensure_loaded(user_id, db_path)

    bill = Bill(
        id=get_next_bill_id(user_id),
        name=name,
        amount=amount,
        due_day=due_day,
        is_paid=is_paid,
    )

    bills[user_id].append(bill)
    save_bills(user_id, db_path)

    logger.info(
        "Added bill %d (%s) for user %d",
        bill.id,
        bill.name,
        user_id,
    )

    return bill


def update_bill(
    user_id: int,
    bill_id: int,
    name: str | None = None,
    amount: Decimal | None = None,
    due_day: int | None = None,
    is_paid: bool | None = None,
    db_path: Path = DB_PATH,
) -> Bill | None:
    """Update one of this user's existing bills."""
    _ensure_loaded(user_id, db_path)

    bill = get_bill_by_id(user_id, bill_id, db_path)

    if bill is None:
        return None

    updated_bill = Bill(
        id=bill.id,
        name=(name.strip() if name is not None else bill.name),
        amount=(amount if amount is not None else bill.amount),
        due_day=(due_day if due_day is not None else bill.due_day),
        is_paid=(is_paid if is_paid is not None else bill.is_paid),
    )

    bill_index = bills[user_id].index(bill)
    bills[user_id][bill_index] = updated_bill

    save_bills(user_id, db_path)

    logger.info(
        "Updated bill %d for user %d",
        bill_id,
        user_id,
    )

    return updated_bill


def mark_bill_paid(
    user_id: int,
    bill_id: int,
    db_path: Path = DB_PATH,
) -> Bill | None:
    """Mark one of this user's bills as paid."""
    return update_bill(
        user_id=user_id,
        bill_id=bill_id,
        is_paid=True,
        db_path=db_path,
    )


def mark_bill_unpaid(
    user_id: int,
    bill_id: int,
    db_path: Path = DB_PATH,
) -> Bill | None:
    """Mark one of this user's bills as unpaid."""
    return update_bill(
        user_id=user_id,
        bill_id=bill_id,
        is_paid=False,
        db_path=db_path,
    )


def delete_bill(user_id: int, bill_id: int, db_path: Path = DB_PATH) -> Bill | None:
    """Delete one of this user's bills by ID."""
    _ensure_loaded(user_id, db_path)

    for index, bill in enumerate(bills[user_id]):
        if bill.id == bill_id:
            deleted_bill = bills[user_id].pop(index)
            save_bills(user_id, db_path)
            logger.info(
                "Deleted bill %d for user %d",
                bill_id,
                user_id,
            )
            return deleted_bill

    return None
