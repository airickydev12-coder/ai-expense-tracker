from src.financial.expense_tracker import expenses, get_total
from src.financial.models import Expense


def test_get_total():
    expenses.clear()

    expenses.append(Expense(id=1, name="Coffee", category="Food", amount=5.25))
    expenses.append(Expense(id=2, name="Tea", category="Food", amount=4.00))

    total = get_total()

    assert total == 9.25