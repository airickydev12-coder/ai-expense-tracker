import pytest

from src.financial.bills.analytics import (
    get_bills_due_soon,
    get_next_unpaid_bill,
    get_paid_bills,
    get_total_bill_amount,
    get_total_unpaid_bill_amount,
    get_unpaid_bills,
)
from src.financial.bills.models import Bill


def build_bills() -> list[Bill]:
    """Create bills for analytics tests."""
    return [
        Bill(
            id=1,
            name="Electric",
            amount=125,
            due_day=15,
            is_paid=False,
        ),
        Bill(
            id=2,
            name="Internet",
            amount=80,
            due_day=20,
            is_paid=True,
        ),
        Bill(
            id=3,
            name="Insurance",
            amount=150,
            due_day=25,
            is_paid=False,
        ),
    ]


def test_get_total_bill_amount():
    assert get_total_bill_amount(build_bills()) == 355


def test_get_total_unpaid_bill_amount():
    assert get_total_unpaid_bill_amount(build_bills()) == 275


def test_get_paid_bills():
    paid_bills = get_paid_bills(build_bills())

    assert len(paid_bills) == 1
    assert paid_bills[0].name == "Internet"


def test_get_unpaid_bills():
    unpaid_bills = get_unpaid_bills(build_bills())

    assert len(unpaid_bills) == 2
    assert unpaid_bills[0].name == "Electric"
    assert unpaid_bills[1].name == "Insurance"


def test_get_bills_due_soon():
    due_soon = get_bills_due_soon(
        build_bills(),
        current_day=10,
        days_ahead=7,
    )

    assert len(due_soon) == 1
    assert due_soon[0].name == "Electric"


def test_get_bills_due_soon_ignores_paid_bills():
    due_soon = get_bills_due_soon(
        build_bills(),
        current_day=18,
        days_ahead=7,
    )

    assert len(due_soon) == 1
    assert due_soon[0].name == "Insurance"


def test_get_bills_due_soon_validates_current_day():
    with pytest.raises(
        ValueError,
        match="between 1 and 31",
    ):
        get_bills_due_soon(
            build_bills(),
            current_day=0,
        )


def test_get_bills_due_soon_validates_days_ahead():
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        get_bills_due_soon(
            build_bills(),
            current_day=10,
            days_ahead=-1,
        )


def test_get_next_unpaid_bill():
    next_bill = get_next_unpaid_bill(
        build_bills(),
        current_day=10,
    )

    assert next_bill is not None
    assert next_bill.name == "Electric"


def test_get_next_unpaid_bill_returns_none():
    next_bill = get_next_unpaid_bill(
        build_bills(),
        current_day=30,
    )

    assert next_bill is None