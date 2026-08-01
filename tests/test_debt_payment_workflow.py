from decimal import Decimal

import pytest

from src.financial.debt.models import Debt
from src.financial.workflows.debt_payment import apply_debt_payment


def test_apply_debt_payment():
    debt = Debt(
        id=1,
        name="Credit Card",
        balance=Decimal("2000.00"),
        interest_rate=19.99,
        minimum_payment=Decimal("50.00"),
    )

    updated = apply_debt_payment(debt, Decimal("500.00"))

    assert updated.balance == 1500


def test_overpayment_sets_balance_to_zero():
    debt = Debt(
        id=1,
        name="Credit Card",
        balance=Decimal("500.00"),
        interest_rate=19.99,
        minimum_payment=Decimal("50.00"),
    )

    updated = apply_debt_payment(debt, Decimal("1000.00"))

    assert updated.balance == 0


def test_negative_payment():
    debt = Debt(
        id=1,
        name="Credit Card",
        balance=Decimal("500.00"),
        interest_rate=19.99,
        minimum_payment=Decimal("50.00"),
    )

    with pytest.raises(ValueError):
        apply_debt_payment(debt, Decimal("-1.00"))
