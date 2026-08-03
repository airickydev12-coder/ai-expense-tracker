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

USER_ID = 1


def setup_function() -> None:
    budgets.clear()


def test_add_budget(db_path):
    budget = add_budget(
        USER_ID,
        ExpenseCategory.FOOD,
        Decimal("500.00"),
        db_path,
    )

    assert budget.limit == 500
    assert budget.category == ExpenseCategory.FOOD


def test_get_budgets(db_path):
    add_budget(
        USER_ID,
        ExpenseCategory.FOOD,
        Decimal("500.00"),
        db_path,
    )

    assert len(get_budgets(USER_ID, db_path)) == 1


def test_get_budget_by_category(db_path):
    add_budget(
        USER_ID,
        ExpenseCategory.FOOD,
        Decimal("500.00"),
        db_path,
    )

    budget = get_budget_by_category(
        USER_ID,
        ExpenseCategory.FOOD,
        db_path,
    )

    assert budget is not None
    assert budget.limit == 500


def test_delete_budget(db_path):
    add_budget(USER_ID, ExpenseCategory.FOOD, Decimal("500.00"), db_path)

    deleted_budget = delete_budget(USER_ID, ExpenseCategory.FOOD, db_path)

    assert deleted_budget is not None
    assert deleted_budget.category == ExpenseCategory.FOOD
    assert len(get_budgets(USER_ID, db_path)) == 0


def test_update_budget_updates_existing_budget(db_path):
    add_budget(
        USER_ID,
        ExpenseCategory.FOOD,
        Decimal("500.00"),
        db_path,
    )

    updated_budget = update_budget(
        USER_ID,
        ExpenseCategory.FOOD,
        Decimal("750.00"),
        db_path,
    )

    assert updated_budget.category == ExpenseCategory.FOOD
    assert updated_budget.limit == 750
    assert len(get_budgets(USER_ID, db_path)) == 1


def test_update_budget_creates_budget_when_missing(db_path):
    updated_budget = update_budget(
        USER_ID,
        ExpenseCategory.FOOD,
        Decimal("600.00"),
        db_path,
    )

    assert updated_budget.category == ExpenseCategory.FOOD
    assert updated_budget.limit == 600
    assert len(get_budgets(USER_ID, db_path)) == 1
