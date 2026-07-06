from src.financial.categories import ExpenseCategory
from src.financial.models import Expense
from src.financial.expense_tracker import expenses
from src.financial.analytics import get_average, get_highest_expense, get_total

def test_get_total():
    expenses.clear()

    expenses.append(
        Expense(id=1, name="Coffee", category=ExpenseCategory.FOOD, amount=5.25)
    )
    expenses.append(
        Expense(id=2, name="Tea", category=ExpenseCategory.FOOD, amount=4.00)
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
            amount=5.00,
        )
    )

    expenses.append(
        Expense(
            id=2,
            name="Lunch",
            category=ExpenseCategory.FOOD,
            amount=15.00,
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
            amount=5.00,
        )
    )

    expenses.append(
        Expense(
            id=2,
            name="Shoes",
            category=ExpenseCategory.CLOTHING,
            amount=120.00,
        )
    )

    highest = get_highest_expense(expenses)

    assert highest is not None
    assert highest.name == "Shoes"
    assert highest.amount == 120.00