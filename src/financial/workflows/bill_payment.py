from src.financial.bills.models import Bill
from src.financial.expenses.models import Expense
from src.financial.expenses.service import add_expense
from src.financial.shared.categories import ExpenseCategory


def pay_bill(user_id: int, bill: Bill) -> Expense:
    """
    Pay a bill and record it as an expense.

    Args:
        user_id: The owning user's ID.
        bill: Bill to pay.

    Returns:
        Expense: The created expense.
    """
    bill.is_paid = True

    return add_expense(
        user_id=user_id,
        name=bill.name,
        category=ExpenseCategory.UTILITIES,
        amount=bill.amount,
    )
