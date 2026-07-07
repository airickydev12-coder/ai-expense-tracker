from src.financial.budgets.analytics import get_budget_summary
from src.financial.budgets.models import Budget
from src.financial.expenses.models import Expense


def build_budget_report(
    budgets: list[Budget],
    expenses: list[Expense],
) -> list[dict]:
    """Build budget report data for all saved budgets."""
    return [get_budget_summary(budget, expenses) for budget in budgets]