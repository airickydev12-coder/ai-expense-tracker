from src.financial.budgets.analytics import get_budget_variance
from src.financial.budgets.models import Budget
from src.financial.shared.categories import ExpenseCategory
from src.financial.expenses.models import Expense
from src.financial.budgets.analytics import (
    get_budget_status,
    get_budget_summary,
    get_budget_variance,
)

from decimal import Decimal


def test_get_budget_variance_under_budget():
    budget = Budget(
        category=ExpenseCategory.FOOD,
        limit=Decimal("100.00"),
    )

    expenses = [
        Expense(
            id=1,
            name="Coffee",
            category=ExpenseCategory.FOOD,
            amount=Decimal("5.00"),
        ),
        Expense(
            id=2,
            name="Lunch",
            category=ExpenseCategory.FOOD,
            amount=Decimal("15.00"),
        ),
    ]

    variance = get_budget_variance(budget, expenses)

    assert variance == 80


def test_get_budget_variance_over_budget():
    budget = Budget(
        category=ExpenseCategory.FOOD,
        limit=Decimal("10.00"),
    )

    expenses = [
        Expense(
            id=1,
            name="Dinner",
            category=ExpenseCategory.FOOD,
            amount=Decimal("25.00"),
        ),
    ]

    variance = get_budget_variance(budget, expenses)

    assert variance == -15


def test_get_budget_variance_ignores_other_categories():
    budget = Budget(
        category=ExpenseCategory.FOOD,
        limit=Decimal("100.00"),
    )

    expenses = [
        Expense(
            id=1,
            name="Gas",
            category=ExpenseCategory.TRANSPORTATION,
            amount=Decimal("50.00"),
        ),
    ]

    variance = get_budget_variance(budget, expenses)

    assert variance == 100


def test_get_budget_status_under_budget():
    budget = Budget(category=ExpenseCategory.FOOD, limit=Decimal("100.00"))
    expenses = [
        Expense(
            id=1, name="Coffee", category=ExpenseCategory.FOOD, amount=Decimal("25.00")
        )
    ]

    assert get_budget_status(budget, expenses) == "Under Budget"


def test_get_budget_status_over_budget():
    budget = Budget(category=ExpenseCategory.FOOD, limit=Decimal("10.00"))
    expenses = [
        Expense(
            id=1, name="Dinner", category=ExpenseCategory.FOOD, amount=Decimal("25.00")
        )
    ]

    assert get_budget_status(budget, expenses) == "Over Budget"


def test_get_budget_status_on_budget():
    budget = Budget(category=ExpenseCategory.FOOD, limit=Decimal("25.00"))
    expenses = [
        Expense(
            id=1, name="Dinner", category=ExpenseCategory.FOOD, amount=Decimal("25.00")
        )
    ]

    assert get_budget_status(budget, expenses) == "On Budget"


def test_get_budget_summary():
    budget = Budget(category=ExpenseCategory.FOOD, limit=Decimal("100.00"))
    expenses = [
        Expense(
            id=1, name="Coffee", category=ExpenseCategory.FOOD, amount=Decimal("5.00")
        ),
        Expense(
            id=2, name="Lunch", category=ExpenseCategory.FOOD, amount=Decimal("15.00")
        ),
    ]

    summary = get_budget_summary(budget, expenses)

    assert summary["category"] == "Food"
    assert summary["limit"] == Decimal("100.00")
    assert summary["spent"] == Decimal("20.00")
    assert summary["remaining"] == Decimal("80.00")
    assert summary["status"] == "Under Budget"
