from src.financial.budgets.models import Budget
from src.financial.expenses.models import Expense
from src.financial.reports.budget_report import build_budget_report
from src.financial.shared.categories import ExpenseCategory


def test_build_budget_report():
    budgets = [
        Budget(category=ExpenseCategory.FOOD, limit=100),
        Budget(category=ExpenseCategory.TRANSPORTATION, limit=50),
    ]

    expenses = [
        Expense(id=1, name="Coffee", category=ExpenseCategory.FOOD, amount=10),
        Expense(id=2, name="Gas", category=ExpenseCategory.TRANSPORTATION, amount=20),
    ]

    report = build_budget_report(budgets, expenses)

    assert len(report) == 2
    assert report[0]["category"] == "Food"
    assert report[0]["remaining"] == 90
    assert report[1]["category"] == "Transportation"
    assert report[1]["remaining"] == 30