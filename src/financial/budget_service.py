from src.financial.budget_models import Budget
from src.financial.budget_repository import (
    load_budgets_from_file,
    save_budgets_to_file,
)
from src.financial.categories import ExpenseCategory


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


def add_budget(category: ExpenseCategory, limit: float) -> Budget:
    """Create and add a new budget."""
    budget = Budget(category=category, limit=limit)
    budgets.append(budget)
    save_budgets()
    return budget