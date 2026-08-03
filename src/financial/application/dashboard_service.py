"""Application service for the financial dashboard."""

from dataclasses import dataclass
from decimal import Decimal

from src.financial.application.financial_snapshot_service import (
    build_financial_snapshot,
)
from src.financial.application.recommendation_application_service import (
    build_recommendations,
)
from src.financial.expenses.models import Expense


@dataclass(frozen=True)
class Dashboard:
    """Represents the application's financial dashboard."""

    total_expenses: Decimal
    average_expense: Decimal

    highest_expense: Expense | None
    lowest_expense: Expense | None

    category_totals: dict[str, Decimal]

    budget_count: int

    monthly_budget: Decimal
    remaining_budget: Decimal
    budget_used_percent: Decimal

    recommendation_count: int

    health_score: int
    health_status: str


def build_dashboard() -> Dashboard:
    """
    Build the financial dashboard.

    This service delegates all financial-fact computation to the canonical
    financial snapshot and recommendation-generation services, so the
    dashboard always reflects the real, current financial state rather than
    recomputing a parallel, easily-drifting copy of it.
    """

    snapshot = build_financial_snapshot()

    # -------------------------
    # Budget Summary
    # -------------------------

    monthly_budget = sum(
        (item["limit"] for item in snapshot.budget_report),
        Decimal("0"),
    )

    remaining_budget = sum(
        (item["remaining"] for item in snapshot.budget_report),
        Decimal("0"),
    )

    spent_budget = sum(
        (item["spent"] for item in snapshot.budget_report),
        Decimal("0"),
    )

    # -------------------------
    # Recommendation Summary
    # -------------------------

    recommendation_count = len(build_recommendations())

    return Dashboard(
        total_expenses=snapshot.total_expenses,
        average_expense=snapshot.average_expense,
        highest_expense=snapshot.highest_expense,
        lowest_expense=snapshot.lowest_expense,
        category_totals=snapshot.category_totals,
        budget_count=snapshot.budget_count,
        monthly_budget=monthly_budget,
        remaining_budget=remaining_budget,
        budget_used_percent=(
            (spent_budget / monthly_budget) * Decimal("100")
            if monthly_budget > Decimal("0")
            else Decimal("0")
        ),
        recommendation_count=recommendation_count,
        health_score=snapshot.health_score,
        health_status=snapshot.health_status,
    )
