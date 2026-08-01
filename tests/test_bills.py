import pytest

from src.financial.bills.models import Bill

from decimal import Decimal


def test_bill_creation():
    bill = Bill(
        id=1,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
    )

    assert bill.name == "Electric"
    assert bill.amount == 125
    assert bill.due_day == 15
    assert bill.is_paid is False


def test_invalid_due_day():
    with pytest.raises(ValueError):
        Bill(
            id=1,
            name="Electric",
            amount=Decimal("125.00"),
            due_day=35,
        )


def test_negative_amount():
    with pytest.raises(ValueError):
        Bill(
            id=1,
            name="Electric",
            amount=Decimal("-10.00"),
            due_day=15,
        )
