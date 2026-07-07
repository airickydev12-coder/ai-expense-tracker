import pytest

from src.financial.debt.models import Debt
from src.financial.workflows.debt_payment import apply_debt_payment


def test_apply_debt_payment():
    debt = Debt(
        id=1,
        name="Credit Card",
        balance=2000,
        interest_rate=19.99,
        minimum_payment=50,
    )

    updated = apply_debt_payment(debt, 500)

    assert updated.balance == 1500


def test_overpayment_sets_balance_to_zero():
    debt = Debt(
        id=1,
        name="Credit Card",
        balance=500,
        interest_rate=19.99,
        minimum_payment=50,
    )

    updated = apply_debt_payment(debt, 1000)

    assert updated.balance == 0


def test_negative_payment():
    debt = Debt(
        id=1,
        name="Credit Card",
        balance=500,
        interest_rate=19.99,
        minimum_payment=50,
    )

    with pytest.raises(ValueError):
        apply_debt_payment(debt, -1)