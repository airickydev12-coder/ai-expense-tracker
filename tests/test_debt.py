from decimal import Decimal

import pytest

from src.financial.debt.models import Debt


def test_debt_creation():
    debt = Debt(
        id=1,
        name="Credit Card",
        balance=Decimal("2500.00"),
        interest_rate=24.99,
        minimum_payment=Decimal("75.00"),
    )

    assert debt.id == 1
    assert debt.name == "Credit Card"
    assert debt.balance == 2500
    assert debt.interest_rate == 24.99
    assert debt.minimum_payment == 75


def test_debt_invalid_id():
    with pytest.raises(ValueError):
        Debt(
            id=0,
            name="Credit Card",
            balance=Decimal("2500.00"),
            interest_rate=24.99,
            minimum_payment=Decimal("75.00"),
        )


def test_debt_empty_name():
    with pytest.raises(ValueError):
        Debt(
            id=1,
            name="",
            balance=Decimal("2500.00"),
            interest_rate=24.99,
            minimum_payment=Decimal("75.00"),
        )


def test_debt_negative_balance():
    with pytest.raises(ValueError):
        Debt(
            id=1,
            name="Credit Card",
            balance=Decimal("-1.00"),
            interest_rate=24.99,
            minimum_payment=Decimal("75.00"),
        )


def test_debt_negative_interest_rate():
    with pytest.raises(ValueError):
        Debt(
            id=1,
            name="Credit Card",
            balance=Decimal("2500.00"),
            interest_rate=-1,
            minimum_payment=Decimal("75.00"),
        )


def test_debt_negative_minimum_payment():
    with pytest.raises(ValueError):
        Debt(
            id=1,
            name="Credit Card",
            balance=Decimal("2500.00"),
            interest_rate=24.99,
            minimum_payment=Decimal("-1.00"),
        )
