"""Application service for building a consolidated financial snapshot."""

from dataclasses import dataclass

from src.financial.budgets import service as budget_service
from src.financial.engine.health_score import calculate_health_score
from src.financial.engine.health_status import get_health_status
from src.financial.expenses import analytics as expense_analytics
from src.financial.expenses import service as expense_service
from src.financial.expenses.models import Expense
from src.financial.goals import service as goal_service


@dataclass(frozen=True)
class FinancialSnapshot:
    """Consolidated representation of the user's current financial state."""

    total_expenses: float
    average_expense: float
    highest_expense: Expense | None
    lowest_expense: Expense | None
    category_totals: dict[str, float]
    budget_count: int
    goal_count: int
    health_score: int
    health_status: str


def build_financial_snapshot() -> FinancialSnapshot:
    """Build and return the current consolidated financial snapshot."""

    expenses = expense_service.get_expenses()
    budgets = budget_service.get_budgets()
    goals = goal_service.get_goals()

    total = expense_analytics.get_total(expenses)
    average = expense_analytics.get_average(expenses)
    highest = expense_analytics.get_highest_expense(expenses)
    lowest = expense_analytics.get_lowest_expense(expenses)
    category_totals = expense_analytics.get_category_totals(expenses)

    budget_count = len(budgets)
    goal_count = len(goals)

    health_snapshot = {
        "net_cash_flow": 0,
        "total_debt": 0,
        "total_account_balance": 0,
        "total_goal_progress": 0,
        "net_worth": 0,
    }

    score = calculate_health_score(health_snapshot)
    status = get_health_status(score)

    return FinancialSnapshot(
        total_expenses=total,
        average_expense=average,
        highest_expense=highest,
        lowest_expense=lowest,
        category_totals=category_totals,
        budget_count=budget_count,
        goal_count=goal_count,
        health_score=score,
        health_status=status,
    )
