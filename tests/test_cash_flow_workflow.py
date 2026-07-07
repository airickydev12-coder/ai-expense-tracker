from src.financial.expenses.models import Expense
from src.financial.income.models import Income
from src.financial.shared.categories import ExpenseCategory
from src.financial.workflows.cash_flow import calculate_cash_flow


def test_calculate_cash_flow():
    income_entries = [
        Income(id=1, source="Salary", amount=5000),
    ]

    expenses = [
        Expense(id=1, name="Rent", category=ExpenseCategory.HOUSING, amount=1200),
        Expense(id=2, name="Food", category=ExpenseCategory.FOOD, amount=300),
    ]

    cash_flow = calculate_cash_flow(income_entries, expenses)

    assert cash_flow["income"] == 5000
    assert cash_flow["expenses"] == 1500
    assert cash_flow["net_cash_flow"] == 3500