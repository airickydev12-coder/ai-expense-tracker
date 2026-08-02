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

    Reads through to_dict() rather than the raw dataclass fields:
    rules access goals/debts/bills/largest_expense by subscript
    (e.g. bill["is_paid"]), which only works against the plain
    dicts to_dict() produces, not the raw Goal/Debt/Bill/Expense
    model instances stored on the snapshot itself.
    """

    data = snapshot.to_dict()

    return {
        # FinancialSnapshot
        "total_expenses": data["total_expenses"],
        "average_expense": data["average_expense"],
        "health_score": data["health_score"],
        "health_status": data["health_status"],
        "category_totals": data["category_totals"],
        # Naming expected by existing rules
        "largest_expense": data["largest_expense"],
        # Goals
        "goals": data["goals"],
        "total_goal_progress": data["total_goal_progress"],
        # Budgets
        "budget_report": data["budget_report"],
        # Bills
        "bills": data["bills"],
        # Debt
        "debts": data["debts"],
        "total_debt": data["total_debt"],
        # Income / Cash Flow
        "total_income": data["total_income"],
        "net_cash_flow": data["net_cash_flow"],
        # Accounts / Net Worth
        "total_account_balance": data["total_account_balance"],
        "net_worth": data["net_worth"],
        # Miscellaneous
        "current_day": data["current_day"],
    }
