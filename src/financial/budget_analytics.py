from src.financial.budget_models import Budget
from src.financial.models import Expense


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
        expense.amount
        for expense in expenses
        if expense.category == budget.category
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