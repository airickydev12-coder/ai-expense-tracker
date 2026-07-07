from src.financial.budget_analytics import get_budget_variance
from src.financial.budget_models import Budget
from src.financial.categories import ExpenseCategory
from src.financial.models import Expense


def test_get_budget_variance_under_budget():
    budget = Budget(
        category=ExpenseCategory.FOOD,
        limit=100,
    )

    expenses = [
        Expense(
            id=1,
            name="Coffee",
            category=ExpenseCategory.FOOD,
            amount=5,
        ),
        Expense(
            id=2,
            name="Lunch",
            category=ExpenseCategory.FOOD,
            amount=15,
        ),
    ]

    variance = get_budget_variance(budget, expenses)

    assert variance == 80


def test_get_budget_variance_over_budget():
    budget = Budget(
        category=ExpenseCategory.FOOD,
        limit=10,
    )

    expenses = [
        Expense(
            id=1,
            name="Dinner",
            category=ExpenseCategory.FOOD,
            amount=25,
        ),
    ]

    variance = get_budget_variance(budget, expenses)

    assert variance == -15


def test_get_budget_variance_ignores_other_categories():
    budget = Budget(
        category=ExpenseCategory.FOOD,
        limit=100,
    )

    expenses = [
        Expense(
            id=1,
            name="Gas",
            category=ExpenseCategory.TRANSPORTATION,
            amount=50,
        ),
    ]

    variance = get_budget_variance(budget, expenses)

    assert variance == 100