from datetime import date

from src.financial.accounts.models import Account
from src.financial.bills.models import Bill
from src.financial.budgets.models import Budget
from src.financial.debt.models import Debt
from src.financial.engine.health_score import calculate_health_score
from src.financial.engine.health_status import get_health_status
from src.financial.expenses.analytics import (
    get_average,
    get_category_totals,
    get_highest_expense,
    get_total,
)
from src.financial.expenses.models import Expense
from src.financial.goals.models import Goal
from src.financial.income.analytics import get_total_income
from src.financial.income.models import Income
from src.financial.insights.insight_engine import generate_insights
from src.financial.recommendations.service import generate_recommendations
from src.financial.reports.budget_report import build_budget_report


def build_financial_snapshot(
    income_entries: list[Income],
    expenses: list[Expense],
    budgets: list[Budget],
    accounts: list[Account],
    goals: list[Goal],
    debts: list[Debt],
    bills: list[Bill] | None = None,
    current_day: int | None = None,
) -> dict:
    """Build a complete financial snapshot."""
    if bills is None:
        bills = []

    if current_day is None:
        current_day = date.today().day

    total_income = get_total_income(income_entries)
    total_expenses = get_total(expenses)
    net_cash_flow = total_income - total_expenses

    average_expense = get_average(expenses)
    largest_expense = get_highest_expense(expenses)
    category_totals = get_category_totals(expenses)

    total_account_balance = sum(account.balance for account in accounts)

    total_goal_progress = sum(goal.current_amount for goal in goals)

    total_debt = sum(debt.balance for debt in debts)

    net_worth = total_account_balance + total_goal_progress - total_debt

    budget_report = build_budget_report(
        budgets,
        expenses,
    )

    health_score = calculate_health_score(
        {
            "net_cash_flow": net_cash_flow,
            "total_debt": total_debt,
            "total_account_balance": total_account_balance,
            "total_goal_progress": total_goal_progress,
            "net_worth": net_worth,
        }
    )

    health_status = get_health_status(health_score)

    insights = generate_insights(
        {
            "net_cash_flow": net_cash_flow,
            "total_debt": total_debt,
            "total_account_balance": total_account_balance,
            "health_score": health_score,
        }
    )

    snapshot = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_cash_flow": net_cash_flow,
        "average_expense": average_expense,
        "largest_expense": (
            {
                "id": largest_expense.id,
                "name": largest_expense.name,
                "category": largest_expense.category.value,
                "amount": largest_expense.amount,
            }
            if largest_expense is not None
            else None
        ),
        "category_totals": category_totals,
        "total_account_balance": total_account_balance,
        "total_goal_progress": total_goal_progress,
        "total_debt": total_debt,
        "net_worth": net_worth,
        "budget_report": budget_report,
        "health_score": health_score,
        "health_status": health_status,
        "accounts": [
            {
                "id": account.id,
                "name": account.name,
                "account_type": account.account_type,
                "balance": account.balance,
            }
            for account in accounts
        ],
        "goals": [
            {
                "id": goal.id,
                "name": goal.name,
                "target_amount": goal.target_amount,
                "current_amount": goal.current_amount,
            }
            for goal in goals
        ],
        "debts": [
            {
                "id": debt.id,
                "name": debt.name,
                "balance": debt.balance,
                "interest_rate": debt.interest_rate,
                "minimum_payment": debt.minimum_payment,
            }
            for debt in debts
        ],
        "bills": [
            {
                "id": bill.id,
                "name": bill.name,
                "amount": bill.amount,
                "due_day": bill.due_day,
                "is_paid": bill.is_paid,
            }
            for bill in bills
        ],
        "current_day": current_day,
        "insights": insights,
    }

    recommendations = generate_recommendations(snapshot)

    snapshot["recommendations"] = [
        recommendation.to_dict() for recommendation in recommendations
    ]

    return snapshot
