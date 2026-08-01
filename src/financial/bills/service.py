from decimal import Decimal
from pathlib import Path

from src.core.logging import get_logger
from src.financial.bills.models import Bill
from src.financial.bills.repository import (
    BILLS_FILE,
    load_bills_from_file,
    save_bills_to_file,
)

logger = get_logger(__name__)

bills: list[Bill] = []


def load_bills(
    file_path: Path = BILLS_FILE,
) -> None:
    """Load bills into application memory."""
    bills.clear()
    bills.extend(load_bills_from_file(file_path))


def save_bills(
    file_path: Path = BILLS_FILE,
) -> None:
    """Save all bills from application memory."""
    save_bills_to_file(
        bills,
        file_path,
    )


def get_bills() -> list[Bill]:
    """Return a copy of all bills."""
    return bills.copy()


def get_bill_by_id(
    bill_id: int,
) -> Bill | None:
    """Return a bill by ID."""
    for bill in bills:
        if bill.id == bill_id:
            return bill

    return None


def get_next_bill_id() -> int:
    """Return the next available bill ID."""
    if not bills:
        return 1

    return max(bill.id for bill in bills) + 1


def add_bill(
    name: str,
    amount: Decimal,
    due_day: int,
    is_paid: bool = False,
    file_path: Path = BILLS_FILE,
) -> Bill:
    """Create and save a bill."""
    bill = Bill(
        id=get_next_bill_id(),
        name=name,
        amount=amount,
        due_day=due_day,
        is_paid=is_paid,
    )

    bills.append(bill)
    save_bills(file_path)

    logger.info(
        "Added bill %d (%s)",
        bill.id,
        bill.name,
    )

    return bill


def update_bill(
    bill_id: int,
    name: str | None = None,
    amount: Decimal | None = None,
    due_day: int | None = None,
    is_paid: bool | None = None,
    file_path: Path = BILLS_FILE,
) -> Bill | None:
    """Update an existing bill."""
    bill = get_bill_by_id(bill_id)

    if bill is None:
        return None

    updated_bill = Bill(
        id=bill.id,
        name=(name.strip() if name is not None else bill.name),
        amount=(amount if amount is not None else bill.amount),
        due_day=(due_day if due_day is not None else bill.due_day),
        is_paid=(is_paid if is_paid is not None else bill.is_paid),
    )

    bill_index = bills.index(bill)
    bills[bill_index] = updated_bill

    save_bills(file_path)

    logger.info(
        "Updated bill %d",
        bill_id,
    )

    return updated_bill


def mark_bill_paid(
    bill_id: int,
    file_path: Path = BILLS_FILE,
) -> Bill | None:
    """Mark an existing bill as paid."""
    return update_bill(
        bill_id=bill_id,
        is_paid=True,
        file_path=file_path,
    )


def mark_bill_unpaid(
    bill_id: int,
    file_path: Path = BILLS_FILE,
) -> Bill | None:
    """Mark an existing bill as unpaid."""
    return update_bill(
        bill_id=bill_id,
        is_paid=False,
        file_path=file_path,
    )


def delete_bill(
    bill_id: int,
    file_path: Path = BILLS_FILE,
) -> Bill | None:
    """Delete a bill by ID."""
    for index, bill in enumerate(bills):
        if bill.id == bill_id:
            deleted_bill = bills.pop(index)
            save_bills(file_path)
            logger.info(
                "Deleted bill %d",
                bill_id,
            )
            return deleted_bill

    return None
