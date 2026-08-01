from decimal import Decimal

from src.financial.budgets.models import Budget
from src.financial.budgets.repository import (
    load_budgets_from_file,
    save_budgets_to_file,
)
from src.financial.shared.categories import ExpenseCategory


budgets: list[Budget] = []


def load_budgets() -> None:
    """Load budgets from the repository."""
    global budgets
    budgets = load_budgets_from_file()


def save_budgets() -> None:
    """Save budgets using the repository."""
    save_budgets_to_file(budgets)


def get_budgets() -> list[Budget]:
    """Return all configured budgets."""
    return budgets.copy()


def add_budget(category: ExpenseCategory, limit: Decimal) -> Budget:
    """Create or update a budget for a category."""
    for budget in budgets:
        if budget.category == category:
            budget.limit = limit
            save_budgets()
            return budget

    budget = Budget(category=category, limit=limit)
    budgets.append(budget)
    save_budgets()

    return budget


def update_budget(
    category: ExpenseCategory,
    limit: Decimal,
) -> Budget:
    """
    Update the budget for a category.

    If the category does not already have a budget,
    one will be created.
    """
    return add_budget(
        category=category,
        limit=limit,
    )


def get_budget_by_category(
    category: ExpenseCategory,
) -> Budget | None:
    """
    Return the budget for a category.

    Args:
        category: Expense category.

    Returns:
        Budget | None: Matching budget, or None if none exists.
    """
    for budget in budgets:
        if budget.category == category:
            return budget

    return None


def delete_budget(category: ExpenseCategory) -> Budget | None:
    """Delete a budget by category."""
    for index, budget in enumerate(budgets):
        if budget.category == category:
            deleted_budget = budgets.pop(index)
            save_budgets()
            return deleted_budget

    return None
