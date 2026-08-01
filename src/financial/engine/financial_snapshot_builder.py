"""Builder for the canonical financial snapshot."""

from datetime import date
from decimal import Decimal

from src.financial.accounts.models import Account
from src.financial.application.financial_snapshot import FinancialSnapshot
from src.financial.bills.models import Bill
from src.financial.budgets.models import Budget
from src.financial.debt.models import Debt
from src.financial.engine.health_score import calculate_health_score
from src.financial.engine.health_status import get_health_status
from src.financial.expenses import analytics as expense_analytics
from src.financial.expenses.models import Expense
from src.financial.goals.models import Goal
from src.financial.income import analytics as income_analytics
from src.financial.income.models import Income
from src.financial.reports.budget_report import build_budget_report

ZERO_MONEY = Decimal("0")


def build_financial_snapshot(
    income_entries: list[Income],
    expenses: list[Expense],
    budgets: list[Budget],
    accounts: list[Account],
    goals: list[Goal],
    debts: list[Debt],
    bills: list[Bill] | None = None,
    current_day: int | None = None,
) -> FinancialSnapshot:
    """
    Build the canonical financial snapshot.

    The builder coordinates existing analytics and calculation modules. It
    does not generate insights, recommendations, forecasts, or coaching
    content.
    """

    snapshot_bills = bills.copy() if bills is not None else []

    snapshot_day = current_day if current_day is not None else date.today().day

    total_income = income_analytics.get_total_income(income_entries)

    total_expenses = expense_analytics.get_total(expenses)

    net_cash_flow = total_income - total_expenses

    average_expense = expense_analytics.get_average(expenses)

    highest_expense = expense_analytics.get_highest_expense(expenses)

    lowest_expense = expense_analytics.get_lowest_expense(expenses)

    category_totals = expense_analytics.get_category_totals(expenses)

    total_account_balance = sum(
        (account.balance for account in accounts),
        ZERO_MONEY,
    )

    total_goal_progress = sum(
        (goal.current_amount for goal in goals),
        ZERO_MONEY,
    )

    total_debt = sum(
        (debt.balance for debt in debts),
        ZERO_MONEY,
    )

    budget_report = build_budget_report(
        budgets,
        expenses,
    )

    net_worth = total_account_balance + total_goal_progress - total_debt

    health_metrics = {
        "net_cash_flow": net_cash_flow,
        "total_debt": total_debt,
        "total_account_balance": total_account_balance,
        "total_goal_progress": total_goal_progress,
        "net_worth": net_worth,
    }

    health_score = calculate_health_score(health_metrics)

    health_status = get_health_status(health_score)

    return FinancialSnapshot(
        total_income=total_income,
        total_expenses=total_expenses,
        net_cash_flow=net_cash_flow,
        average_expense=average_expense,
        highest_expense=highest_expense,
        lowest_expense=lowest_expense,
        category_totals=category_totals,
        budget_count=len(budgets),
        goal_count=len(goals),
        budget_report=budget_report,
        total_account_balance=total_account_balance,
        total_goal_progress=total_goal_progress,
        total_debt=total_debt,
        net_worth=net_worth,
        accounts=accounts.copy(),
        goals=goals.copy(),
        debts=debts.copy(),
        bills=snapshot_bills,
        current_day=snapshot_day,
        health_score=health_score,
        health_status=health_status,
    )
