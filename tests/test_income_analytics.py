from src.financial.income.analytics import (
    get_average_income,
    get_highest_income,
    get_total_income,
)
from src.financial.income.models import Income

from decimal import Decimal


def test_get_total_income():
    income_entries = [
        Income(id=1, source="Salary", amount=Decimal("5000.00")),
        Income(id=2, source="Freelance", amount=Decimal("1000.00")),
    ]

    assert get_total_income(income_entries) == 6000


def test_get_average_income():
    income_entries = [
        Income(id=1, source="Salary", amount=Decimal("5000.00")),
        Income(id=2, source="Freelance", amount=Decimal("1000.00")),
    ]

    assert get_average_income(income_entries) == 3000


def test_get_highest_income():
    income_entries = [
        Income(id=1, source="Salary", amount=Decimal("5000.00")),
        Income(id=2, source="Freelance", amount=Decimal("1000.00")),
    ]

    highest = get_highest_income(income_entries)

    assert highest is not None
    assert highest.source == "Salary"
