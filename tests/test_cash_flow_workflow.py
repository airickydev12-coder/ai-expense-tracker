from decimal import Decimal

from src.financial.expenses.models import Expense
from src.financial.income.models import Income
from src.financial.shared.categories import ExpenseCategory
from src.financial.workflows.cash_flow import calculate_cash_flow


def test_calculate_cash_flow():
    income_entries = [
        Income(id=1, source="Salary", amount=Decimal("5000.00")),
    ]

    expenses = [
        Expense(
            id=1,
            name="Rent",
            category=ExpenseCategory.HOUSING,
            amount=Decimal("1200.00"),
        ),
        Expense(
            id=2, name="Food", category=ExpenseCategory.FOOD, amount=Decimal("300.00")
        ),
    ]

    cash_flow = calculate_cash_flow(income_entries, expenses)

    assert cash_flow["income"] == Decimal("5000.00")
    assert cash_flow["expenses"] == Decimal("1500.00")
    assert cash_flow["net_cash_flow"] == Decimal("3500.00")
