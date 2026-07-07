from src.financial.budgets.service import (
    add_budget,
    budgets,
    get_budget_by_category,
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

def test_get_budget_by_category():
    budgets.clear()

    add_budget(
        ExpenseCategory.FOOD,
        500,
    )

    budget = get_budget_by_category(
        ExpenseCategory.FOOD,
    )

    assert budget is not None
    assert budget.limit == 500
