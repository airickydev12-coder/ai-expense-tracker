"""Application service for building the current financial snapshot."""

from src.financial.application.financial_snapshot import FinancialSnapshot
from src.financial.budgets import service as budget_service
from src.financial.engine.financial_snapshot_builder import (
    build_financial_snapshot as build_snapshot,
)
from src.financial.expenses import service as expense_service
from src.financial.goals import service as goal_service
from src.financial.income import service as income_service
from src.financial.accounts import service as account_service
from src.financial.debt import service as debt_service
from src.financial.bills import service as bill_service


def build_financial_snapshot() -> FinancialSnapshot:
    """
    Build and return the current canonical financial snapshot.

    This service retrieves stored application data and delegates all
    financial calculations to the canonical snapshot builder.
    """

    income_entries = income_service.get_income_entries()
    expenses = expense_service.get_expenses()
    budgets = budget_service.get_budgets()
    accounts = account_service.get_accounts()
    goals = goal_service.get_goals()
    debts = debt_service.get_debts()
    bills = bill_service.get_bills()

    return build_snapshot(
        income_entries=income_entries,
        expenses=expenses,
        budgets=budgets,
        accounts=accounts,
        goals=goals,
        debts=debts,
        bills=bills,
    )
