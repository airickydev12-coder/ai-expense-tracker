import pytest

from src.financial.income.models import Income


def test_income_creation():
    income = Income(id=1, source="Salary", amount=5000)

    assert income.id == 1
    assert income.source == "Salary"
    assert income.amount == 5000


def test_income_empty_source():
    with pytest.raises(ValueError):
        Income(id=1, source="", amount=5000)


def test_income_negative_amount():
    with pytest.raises(ValueError):
        Income(id=1, source="Salary", amount=-100)


def test_income_invalid_id():
    with pytest.raises(ValueError):
        Income(id=0, source="Salary", amount=5000)