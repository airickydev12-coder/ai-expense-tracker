from src.financial.income.analytics import (
    get_average_income,
    get_highest_income,
    get_total_income,
)
from src.financial.income.models import Income


def test_get_total_income():
    income_entries = [
        Income(id=1, source="Salary", amount=5000),
        Income(id=2, source="Freelance", amount=1000),
    ]

    assert get_total_income(income_entries) == 6000


def test_get_average_income():
    income_entries = [
        Income(id=1, source="Salary", amount=5000),
        Income(id=2, source="Freelance", amount=1000),
    ]

    assert get_average_income(income_entries) == 3000


def test_get_highest_income():
    income_entries = [
        Income(id=1, source="Salary", amount=5000),
        Income(id=2, source="Freelance", amount=1000),
    ]

    highest = get_highest_income(income_entries)

    assert highest is not None
    assert highest.source == "Salary"