from decimal import Decimal

from src.financial.budgets.service import (
    add_budget,
    budgets,
    delete_budget,
    get_budget_by_category,
    get_budgets,
    update_budget,
)
from src.financial.shared.categories import ExpenseCategory


def test_add_budget():
    budgets.clear()

    budget = add_budget(
        ExpenseCategory.FOOD,
        Decimal("500.00"),
    )

    assert budget.limit == 500
    assert budget.category == ExpenseCategory.FOOD


def test_get_budgets():
    budgets.clear()

    add_budget(
        ExpenseCategory.FOOD,
        Decimal("500.00"),
    )

    assert len(get_budgets()) == 1


def test_get_budget_by_category():
    budgets.clear()

    add_budget(
        ExpenseCategory.FOOD,
        Decimal("500.00"),
    )

    budget = get_budget_by_category(
        ExpenseCategory.FOOD,
    )

    assert budget is not None
    assert budget.limit == 500


def test_delete_budget():
    budgets.clear()

    add_budget(ExpenseCategory.FOOD, Decimal("500.00"))

    deleted_budget = delete_budget(ExpenseCategory.FOOD)

    assert deleted_budget is not None
    assert deleted_budget.category == ExpenseCategory.FOOD
    assert len(get_budgets()) == 0


def test_update_budget_updates_existing_budget():
    budgets.clear()

    add_budget(
        ExpenseCategory.FOOD,
        Decimal("500.00"),
    )

    updated_budget = update_budget(
        ExpenseCategory.FOOD,
        Decimal("750.00"),
    )

    assert updated_budget.category == ExpenseCategory.FOOD
    assert updated_budget.limit == 750
    assert len(get_budgets()) == 1


def test_update_budget_creates_budget_when_missing():
    budgets.clear()

    updated_budget = update_budget(
        ExpenseCategory.FOOD,
        Decimal("600.00"),
    )

    assert updated_budget.category == ExpenseCategory.FOOD
    assert updated_budget.limit == 600
    assert len(get_budgets()) == 1
