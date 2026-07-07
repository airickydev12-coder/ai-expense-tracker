from src.financial.budget_service import (
    add_budget,
    budgets,
    get_budgets,
)
from src.financial.categories import ExpenseCategory


def test_add_budget():
    budgets.clear()

    budget = add_budget(
        ExpenseCategory.FOOD,
        500,
    )

    assert budget.limit == 500
    assert budget.category == ExpenseCategory.FOOD


def test_get_budgets():
    budgets.clear()

    add_budget(
        ExpenseCategory.FOOD,
        500,
    )

    assert len(get_budgets()) == 1