import pytest

from src.financial.budgets.models import Budget
from src.financial.shared.categories import ExpenseCategory

from decimal import Decimal


def test_budget_creation():
    budget = Budget(
        category=ExpenseCategory.FOOD,
        limit=Decimal("500.00"),
    )

    assert budget.limit == Decimal("500.00")
    assert budget.category == ExpenseCategory.FOOD


def test_negative_budget():
    with pytest.raises(ValueError):
        Budget(
            category=ExpenseCategory.FOOD,
            limit=Decimal("-10.00"),
        )
