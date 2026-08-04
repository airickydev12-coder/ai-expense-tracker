"""Application service for building the current financial snapshot."""

from src.financial.accounts import service as account_service
from src.financial.application.financial_snapshot import FinancialSnapshot
from src.financial.bills import service as bill_service
from src.financial.budgets import service as budget_service
from src.financial.debt import service as debt_service
from src.financial.engine.financial_snapshot_builder import (
    build_financial_snapshot as build_snapshot,
)
from src.financial.expenses import service as expense_service
from src.financial.goals import service as goal_service
from src.financial.income import service as income_service


def build_financial_snapshot(user_id: int) -> FinancialSnapshot:
    """
    Build and return this user's current canonical financial snapshot.

    This service retrieves stored application data and delegates all
    financial calculations to the canonical snapshot builder.
    """

    income_entries = income_service.get_income_entries(user_id)
    expenses = expense_service.get_expenses(user_id)
    budgets = budget_service.get_budgets(user_id)
    accounts = account_service.get_accounts(user_id)
    goals = goal_service.get_goals(user_id)
    debts = debt_service.get_debts(user_id)
    bills = bill_service.get_bills(user_id)

    return build_snapshot(
        income_entries=income_entries,
        expenses=expenses,
        budgets=budgets,
        accounts=accounts,
        goals=goals,
        debts=debts,
        bills=bills,
    )
