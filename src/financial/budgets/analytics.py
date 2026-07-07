from src.financial.budgets.models import Budget
from src.financial.expenses.models import Expense


def get_budget_variance(
    budget: Budget,
    expenses: list[Expense],
) -> float:
    """
    Calculate the remaining budget after expenses.

    Positive value means under budget.
    Negative value means over budget.

    Args:
        budget: Budget to compare against.
        expenses: Expenses to compare.

    Returns:
        float: Budget limit minus total spending for that category.
    """
    spent = sum(
        expense.amount for expense in expenses if expense.category == budget.category
    )

    return budget.limit - spent


def get_budget_status(
    budget: Budget,
    expenses: list[Expense],
) -> str:
    """
    Return budget status based on remaining budget.

    Returns:
        str: "Under Budget", "On Budget", or "Over Budget".
    """
    variance = get_budget_variance(budget, expenses)

    if variance > 0:
        return "Under Budget"

    if variance < 0:
        return "Over Budget"

    return "On Budget"


def get_budget_summary(
    budget: Budget,
    expenses: list[Expense],
) -> dict:
    """
    Return a summary of budget performance.

    Args:
        budget: Budget to evaluate.
        expenses: Expenses to compare.

    Returns:
        dict: Budget summary data.
    """
    spent = sum(
        expense.amount for expense in expenses if expense.category == budget.category
    )
    remaining = get_budget_variance(budget, expenses)
    status = get_budget_status(budget, expenses)

    return {
        "category": budget.category.value,
        "limit": budget.limit,
        "spent": spent,
        "remaining": remaining,
        "status": status,
    }
