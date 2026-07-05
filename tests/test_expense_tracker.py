from src.financial.expense_tracker import expenses, get_total
from src.financial.models import Expense


def test_get_total():
    expenses.clear()

    expenses.append(Expense(name="Coffee", category="Food", amount=5.25))
    expenses.append(Expense(name="Tea", category="Food", amount=4.00))

    total = get_total()

    assert total == 9.25