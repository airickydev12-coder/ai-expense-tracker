from src.financial.budgets.service import (
    add_budget,
    update_budget,
    budgets,
    get_budget_by_category,
    get_budgets,
    delete_budget,
)

from src.financial.shared.categories import ExpenseCategory


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


def test_delete_budget():
    budgets.clear()

    add_budget(ExpenseCategory.FOOD, 500)

    deleted_budget = delete_budget(ExpenseCategory.FOOD)

    assert deleted_budget is not None
    assert deleted_budget.category == ExpenseCategory.FOOD
    assert len(get_budgets()) == 0


def test_update_budget_updates_existing_budget():
    budgets.clear()

    add_budget(
        ExpenseCategory.FOOD,
        500,
    )

    updated_budget = update_budget(
        ExpenseCategory.FOOD,
        750,
    )

    assert updated_budget.category == ExpenseCategory.FOOD
    assert updated_budget.limit == 750
    assert len(get_budgets()) == 1


def test_update_budget_creates_budget_when_missing():
    budgets.clear()

    updated_budget = update_budget(
        ExpenseCategory.FOOD,
        600,
    )

    assert updated_budget.category == ExpenseCategory.FOOD
    assert updated_budget.limit == 600
    assert len(get_budgets()) == 1
