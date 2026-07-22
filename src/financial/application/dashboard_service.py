"""Application service for the financial dashboard."""

from dataclasses import dataclass

from src.financial.budgets.models import Budget
from src.financial.budgets.service import get_budgets
from src.financial.engine.health_score import calculate_health_score
from src.financial.engine.health_status import get_health_status
from src.financial.expenses import analytics as expense_analytics
from src.financial.expenses.models import Expense
from src.financial.expenses.service import get_expenses
from src.financial.reports.budget_report import build_budget_report


@dataclass(frozen=True)
class Dashboard:
    """Represents the application's financial dashboard."""

    total_expenses: float
    average_expense: float

    highest_expense: Expense | None
    lowest_expense: Expense | None

    category_totals: dict[str, float]

    budget_count: int

    monthly_budget: float
    remaining_budget: float
    budget_used_percent: float

    recommendation_count: int

    health_score: int
    health_status: str


def build_dashboard() -> Dashboard:
    """
    Build the financial dashboard.

    This service orchestrates existing financial services and
    analytics modules. It intentionally performs only lightweight
    aggregation while reusing existing business calculations.
    """

    # -------------------------
    # Expense Analytics
    # -------------------------

    expenses = get_expenses()

    total = expense_analytics.get_total(expenses)

    average = expense_analytics.get_average(expenses)

    highest = expense_analytics.get_highest_expense(expenses)

    lowest = expense_analytics.get_lowest_expense(expenses)

    category_totals = expense_analytics.get_category_totals(expenses)

    # -------------------------
    # Budget Summary
    # -------------------------

    budgets: list[Budget] = get_budgets()

    budget_count = len(budgets)

    budget_report = build_budget_report(
        budgets,
        expenses,
    )

    monthly_budget = sum(item["limit"] for item in budget_report)

    remaining_budget = sum(item["remaining"] for item in budget_report)

    spent_budget = sum(item["spent"] for item in budget_report)

    budget_used_percent = (
        (spent_budget / monthly_budget) * 100 if monthly_budget > 0 else 0.0
    )

    # -------------------------
    # Recommendation Summary
    # -------------------------

    recommendation_count = 0

    # -------------------------
    # Financial Health
    # -------------------------

    snapshot = {
        "net_cash_flow": 0,
        "total_debt": 0,
        "total_account_balance": 0,
        "total_goal_progress": 0,
        "net_worth": 0,
    }

    score = calculate_health_score(snapshot)

    status = get_health_status(score)

    return Dashboard(
        total_expenses=total,
        average_expense=average,
        highest_expense=highest,
        lowest_expense=lowest,
        category_totals=category_totals,
        budget_count=budget_count,
        monthly_budget=monthly_budget,
        remaining_budget=remaining_budget,
        budget_used_percent=budget_used_percent,
        recommendation_count=recommendation_count,
        health_score=score,
        health_status=status,
    )
