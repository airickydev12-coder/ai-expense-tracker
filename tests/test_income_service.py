from src.financial.income.service import (
    add_income,
    delete_income,
    get_income_entries,
    income_entries,
)

from decimal import Decimal


def test_add_income():
    income_entries.clear()

    income = add_income("Salary", Decimal("5000.00"))

    assert income.id == 1
    assert income.source == "Salary"
    assert income.amount == Decimal("5000.00")


def test_get_income_entries():
    income_entries.clear()

    add_income("Salary", Decimal("5000.00"))

    assert len(get_income_entries()) == 1


def test_delete_income():
    income_entries.clear()

    add_income("Salary", Decimal("5000.00"))

    deleted_income = delete_income(1)

    assert deleted_income is not None
    assert deleted_income.source == "Salary"
    assert len(get_income_entries()) == 0
