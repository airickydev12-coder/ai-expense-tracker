"""Adapter for converting FinancialSnapshot into a rule-engine snapshot."""

from src.financial.application.financial_snapshot_service import (
    FinancialSnapshot,
)


def build_rule_snapshot(
    snapshot: FinancialSnapshot,
) -> dict:
    """
    Convert a FinancialSnapshot into the dictionary expected
    by the financial rule engine.

    Placeholder values are included for domains that have not
    yet been integrated (debts, bills, income, accounts, etc.).
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
        "goals": [],
        "total_goal_progress": 0.0,
        # Budgets
        "budget_report": {},
        # Bills
        "bills": [],
        # Debt
        "debts": [],
        "total_debt": 0.0,
        # Income / Cash Flow
        "total_income": 0.0,
        "net_cash_flow": 0.0,
        # Accounts / Net Worth
        "total_account_balance": 0.0,
        "net_worth": 0.0,
        # Miscellaneous
        "current_day": None,
    }
