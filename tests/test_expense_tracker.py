from src.financial.categories import ExpenseCategory
from src.financial.models import Expense
from src.financial.analytics import get_total
from src.financial.expense_tracker import expenses
from src.financial.analytics import get_average

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