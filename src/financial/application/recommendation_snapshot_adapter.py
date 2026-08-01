"""Adapter for converting FinancialSnapshot into a rule-engine snapshot."""

from src.financial.application.financial_snapshot_service import (
    FinancialSnapshot,
)


def build_rule_snapshot(
    snapshot: FinancialSnapshot,
) -> dict:
    """
    Convert a FinancialSnapshot into the dictionary
    consumed by the recommendation rule engine.

    This adapter maps the canonical FinancialSnapshot
    to the field names expected by the existing
    recommendation rules.
    """

    return {
        # FinancialSnapshot
        "total_expenses": snapshot.total_expenses,
        "average_expense": snapshot.average_expense,
        "health_score": snapshot.health_score,
        "health_status": snapshot.health_status,
        "category_totals": snapshot.category_totals,
        # Naming expected by existing rules
        "largest_expense": snapshot.highest_expense,
        # Goals
        "goals": snapshot.goals,
        "total_goal_progress": snapshot.total_goal_progress,
        # Budgets
        "budget_report": snapshot.budget_report,
        # Bills
        "bills": snapshot.bills,
        # Debt
        "debts": snapshot.debts,
        "total_debt": snapshot.total_debt,
        # Income / Cash Flow
        "total_income": snapshot.total_income,
        "net_cash_flow": snapshot.net_cash_flow,
        # Accounts / Net Worth
        "total_account_balance": snapshot.total_account_balance,
        "net_worth": snapshot.net_worth,
        # Miscellaneous
        "current_day": snapshot.current_day,
    }
