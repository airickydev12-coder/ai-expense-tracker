from src.financial.budget_models import Budget
from src.financial.categories import ExpenseCategory

budgets: list[Budget] = []


def get_budgets() -> list[Budget]:
    """
    Return all configured budgets.

    Returns:
        list[Budget]: A copy of the current budgets.
    """
    return budgets.copy()


def add_budget(category: ExpenseCategory, limit: float) -> Budget:
    """
    Create and add a new budget.

    Args:
        category: Expense category.
        limit: Spending limit.

    Returns:
        Budget: The created budget.
    """
    budget = Budget(
        category=category,
        limit=limit,
    )

    budgets.append(budget)

    return budget