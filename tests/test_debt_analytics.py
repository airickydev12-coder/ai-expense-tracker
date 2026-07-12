from src.financial.debt.analytics import (
    get_debt_count,
    get_highest_interest_debt,
    get_total_debt,
    get_total_minimum_payments,
    is_debt_paid_off,
)
from src.financial.debt.models import Debt


def build_debts() -> list[Debt]:
    """Create debt records for analytics tests."""
    return [
        Debt(
            id=1,
            name="Credit Card",
            balance=2500,
            interest_rate=24.99,
            minimum_payment=75,
        ),
        Debt(
            id=2,
            name="Car Loan",
            balance=12000,
            interest_rate=6.5,
            minimum_payment=350,
        ),
        Debt(
            id=3,
            name="Paid Loan",
            balance=0,
            interest_rate=10,
            minimum_payment=100,
        ),
    ]


def test_get_total_debt():
    assert get_total_debt(build_debts()) == 14500


def test_get_total_minimum_payments():
    assert get_total_minimum_payments(build_debts()) == 425


def test_get_highest_interest_debt():
    result = get_highest_interest_debt(build_debts())

    assert result is not None
    assert result.name == "Credit Card"


def test_get_highest_interest_debt_returns_none_without_active_debt():
    debts = [
        Debt(
            id=1,
            name="Paid Loan",
            balance=0,
            interest_rate=10,
            minimum_payment=100,
        )
    ]

    assert get_highest_interest_debt(debts) is None


def test_get_debt_count():
    assert get_debt_count(build_debts()) == 2


def test_is_debt_paid_off():
    debt = Debt(
        id=1,
        name="Paid Loan",
        balance=0,
        interest_rate=10,
        minimum_payment=100,
    )

    assert is_debt_paid_off(debt) is True


def test_is_debt_not_paid_off():
    debt = Debt(
        id=1,
        name="Credit Card",
        balance=2500,
        interest_rate=24.99,
        minimum_payment=75,
    )

    assert is_debt_paid_off(debt) is False