from src.financial.income.service import (
    add_income,
    delete_income,
    get_income_entries,
    income_entries,
)


def test_add_income():
    income_entries.clear()

    income = add_income("Salary", 5000)

    assert income.id == 1
    assert income.source == "Salary"
    assert income.amount == 5000


def test_get_income_entries():
    income_entries.clear()

    add_income("Salary", 5000)

    assert len(get_income_entries()) == 1


def test_delete_income():
    income_entries.clear()

    add_income("Salary", 5000)

    deleted_income = delete_income(1)

    assert deleted_income is not None
    assert deleted_income.source == "Salary"
    assert len(get_income_entries()) == 0