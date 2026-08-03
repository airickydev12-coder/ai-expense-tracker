from decimal import Decimal

from src.financial.income.service import (
    add_income,
    delete_income,
    get_income_entries,
    income_entries,
)

USER_ID = 1


def test_add_income(db_path):
    income_entries.clear()

    income = add_income(USER_ID, "Salary", Decimal("5000.00"), db_path)

    assert income.id == 1
    assert income.source == "Salary"
    assert income.amount == Decimal("5000.00")


def test_get_income_entries(db_path):
    income_entries.clear()

    add_income(USER_ID, "Salary", Decimal("5000.00"), db_path)

    assert len(get_income_entries(USER_ID, db_path)) == 1


def test_delete_income(db_path):
    income_entries.clear()

    add_income(USER_ID, "Salary", Decimal("5000.00"), db_path)

    deleted_income = delete_income(USER_ID, 1, db_path)

    assert deleted_income is not None
    assert deleted_income.source == "Salary"
    assert len(get_income_entries(USER_ID, db_path)) == 0
