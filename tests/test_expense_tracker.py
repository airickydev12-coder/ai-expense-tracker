from decimal import Decimal

from src.financial.expenses.analytics import (
    get_average,
    get_category_totals,
    get_highest_expense,
    get_lowest_expense,
    get_total,
)
from src.financial.expenses.models import Expense
from src.financial.expenses.service import expenses
from src.financial.shared.categories import ExpenseCategory


def test_get_total():
    expenses.clear()

    expenses.append(
        Expense(
            id=1, name="Coffee", category=ExpenseCategory.FOOD, amount=Decimal("5.25")
        )
    )
    expenses.append(
        Expense(id=2, name="Tea", category=ExpenseCategory.FOOD, amount=Decimal("4.00"))
    )

    total = get_total(expenses)

    assert total == 9.25


def test_get_average():
    expenses.clear()

    expenses.append(
        Expense(
            id=1,
            name="Coffee",
            category=ExpenseCategory.FOOD,
            amount=Decimal("5.00"),
        )
    )

    expenses.append(
        Expense(
            id=2,
            name="Lunch",
            category=ExpenseCategory.FOOD,
            amount=Decimal("15.00"),
        )
    )

    average = get_average(expenses)

    assert average == 10.00


def test_get_highest_expense():
    expenses.clear()

    expenses.append(
        Expense(
            id=1,
            name="Coffee",
            category=ExpenseCategory.FOOD,
            amount=Decimal("5.00"),
        )
    )

    expenses.append(
        Expense(
            id=2,
            name="Shoes",
            category=ExpenseCategory.CLOTHING,
            amount=Decimal("120.00"),
        )
    )

    highest = get_highest_expense(expenses)

    assert highest is not None
    assert highest.name == "Shoes"
    assert highest.amount == Decimal("120.00")


def test_get_lowest_expense():
    expenses.clear()

    expenses.append(
        Expense(
            id=1,
            name="Coffee",
            category=ExpenseCategory.FOOD,
            amount=Decimal("5.00"),
        )
    )

    expenses.append(
        Expense(
            id=2,
            name="Shoes",
            category=ExpenseCategory.CLOTHING,
            amount=Decimal("120.00"),
        )
    )

    lowest = get_lowest_expense(expenses)

    assert lowest is not None
    assert lowest.name == "Coffee"
    assert lowest.amount == Decimal("5.00")


def test_get_category_totals():
    expenses.clear()

    expenses.append(
        Expense(
            id=1,
            name="Coffee",
            category=ExpenseCategory.FOOD,
            amount=Decimal("5.00"),
        )
    )

    expenses.append(
        Expense(
            id=2,
            name="Lunch",
            category=ExpenseCategory.FOOD,
            amount=Decimal("15.00"),
        )
    )

    expenses.append(
        Expense(
            id=3,
            name="Gas",
            category=ExpenseCategory.TRANSPORTATION,
            amount=Decimal("40.00"),
        )
    )

    totals = get_category_totals(expenses)

    assert totals["Food"] == Decimal("20.00")
    assert totals["Transportation"] == Decimal("40.00")
