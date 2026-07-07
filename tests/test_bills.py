import pytest

from src.financial.bills.models import Bill


def test_bill_creation():
    bill = Bill(
        id=1,
        name="Electric",
        amount=125,
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
            amount=125,
            due_day=35,
        )


def test_negative_amount():
    with pytest.raises(ValueError):
        Bill(
            id=1,
            name="Electric",
            amount=-10,
            due_day=15,
        )