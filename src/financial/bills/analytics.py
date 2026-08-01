from src.financial.bills.models import Bill
from decimal import Decimal

from src.core.exceptions import ValidationError


def get_total_bill_amount(
    bills: list[Bill],
) -> Decimal:
    """Return the total amount of all bills."""
    return sum(
        (bill.amount for bill in bills),
        start=Decimal("0"),
    )


def get_total_unpaid_bill_amount(
    bills: list[Bill],
) -> Decimal:
    """Return the total amount of unpaid bills."""
    return sum(
        (bill.amount for bill in bills if not bill.is_paid),
        start=Decimal("0"),
    )


def get_paid_bills(
    bills: list[Bill],
) -> list[Bill]:
    """Return all paid bills."""
    return [bill for bill in bills if bill.is_paid]


def get_unpaid_bills(
    bills: list[Bill],
) -> list[Bill]:
    """Return all unpaid bills."""
    return [bill for bill in bills if not bill.is_paid]


def get_bills_due_soon(
    bills: list[Bill],
    current_day: int,
    days_ahead: int = 7,
) -> list[Bill]:
    """Return unpaid bills due within the requested day range."""
    if current_day < 1 or current_day > 31:
        raise ValidationError("Current day must be between 1 and 31.")

    if days_ahead < 0:
        raise ValidationError("Days ahead cannot be negative.")

    return [
        bill
        for bill in bills
        if (not bill.is_paid and 0 <= bill.due_day - current_day <= days_ahead)
    ]


def get_next_unpaid_bill(
    bills: list[Bill],
    current_day: int,
) -> Bill | None:
    """Return the next unpaid bill due on or after the current day."""
    upcoming_bills = [
        bill for bill in bills if (not bill.is_paid and bill.due_day >= current_day)
    ]

    if not upcoming_bills:
        return None

    return min(
        upcoming_bills,
        key=lambda bill: bill.due_day,
    )
