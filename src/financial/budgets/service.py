from decimal import Decimal
from pathlib import Path

from src.core.config import DB_PATH
from src.core.logging import get_logger
from src.financial.budgets.models import Budget
from src.financial.budgets.repository import (
    load_budgets_from_file,
    save_budgets_to_file,
)
from src.financial.shared.categories import ExpenseCategory

logger = get_logger(__name__)

budgets: dict[int, list[Budget]] = {}


def _ensure_loaded(user_id: int, db_path: Path = DB_PATH) -> None:
    """Lazily load a user's budgets into the cache on first access."""
    if user_id not in budgets:
        budgets[user_id] = load_budgets_from_file(user_id, db_path)


def load_budgets(user_id: int, db_path: Path = DB_PATH) -> None:
    """Force-reload a user's budgets from the repository."""
    budgets[user_id] = load_budgets_from_file(user_id, db_path)


def save_budgets(user_id: int, db_path: Path = DB_PATH) -> None:
    """Save a user's budgets using the repository."""
    save_budgets_to_file(budgets[user_id], user_id, db_path)


def get_budgets(user_id: int, db_path: Path = DB_PATH) -> list[Budget]:
    """Return all of this user's configured budgets."""
    _ensure_loaded(user_id, db_path)
    return budgets[user_id].copy()


def add_budget(
    user_id: int,
    category: ExpenseCategory,
    limit: Decimal,
    db_path: Path = DB_PATH,
) -> Budget:
    """Create or update this user's budget for a category."""
    _ensure_loaded(user_id, db_path)

    for budget in budgets[user_id]:
        if budget.category == category:
            budget.limit = limit
            save_budgets(user_id, db_path)
            logger.info(
                "Updated budget for %s for user %d",
                category.value,
                user_id,
            )
            return budget

    budget = Budget(category=category, limit=limit)
    budgets[user_id].append(budget)
    save_budgets(user_id, db_path)

    logger.info(
        "Added budget for %s for user %d",
        category.value,
        user_id,
    )

    return budget


def update_budget(
    user_id: int,
    category: ExpenseCategory,
    limit: Decimal,
    db_path: Path = DB_PATH,
) -> Budget:
    """
    Update the budget for a category.

    If the category does not already have a budget,
    one will be created.
    """
    return add_budget(
        user_id=user_id,
        category=category,
        limit=limit,
        db_path=db_path,
    )


def get_budget_by_category(
    user_id: int,
    category: ExpenseCategory,
    db_path: Path = DB_PATH,
) -> Budget | None:
    """
    Return this user's budget for a category.

    Args:
        user_id: The owning user's ID.
        category: Expense category.
        db_path: Database path override, mainly for tests.

    Returns:
        Budget | None: Matching budget, or None if none exists.
    """
    _ensure_loaded(user_id, db_path)

    for budget in budgets[user_id]:
        if budget.category == category:
            return budget

    return None


def delete_budget(user_id: int, category: ExpenseCategory, db_path: Path = DB_PATH) -> Budget | None:
    """Delete this user's budget by category."""
    _ensure_loaded(user_id, db_path)

    for index, budget in enumerate(budgets[user_id]):
        if budget.category == category:
            deleted_budget = budgets[user_id].pop(index)
            save_budgets(user_id, db_path)
            logger.info(
                "Deleted budget for %s for user %d",
                category.value,
                user_id,
            )
            return deleted_budget

    return None
