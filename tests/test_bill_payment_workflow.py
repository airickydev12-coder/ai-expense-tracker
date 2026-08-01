from src.financial.bills.models import Bill
from src.financial.expenses.service import expenses
from src.financial.shared.categories import ExpenseCategory
from src.financial.workflows.bill_payment import pay_bill

from decimal import Decimal


def test_pay_bill_creates_expense():
    expenses.clear()

    bill = Bill(
        id=1,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
    )

    expense = pay_bill(bill)

    assert bill.is_paid is True
    assert expense.name == "Electric"
    assert expense.amount == Decimal("125.00")
    assert expense.category == ExpenseCategory.UTILITIES
    assert len(expenses) == 1
