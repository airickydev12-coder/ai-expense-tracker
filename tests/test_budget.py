import pytest

from src.financial.budget_models import Budget
from src.financial.categories import ExpenseCategory


def test_budget_creation():
    budget = Budget(
        category=ExpenseCategory.FOOD,
        limit=500,
    )

    assert budget.limit == 500
    assert budget.category == ExpenseCategory.FOOD


def test_negative_budget():
    with pytest.raises(ValueError):
        Budget(
            category=ExpenseCategory.FOOD,
            limit=-10,
        )