from src.financial.accounts.models import Account
from src.financial.application.recommendation_snapshot_adapter import (
    build_rule_snapshot,
)
from src.financial.bills.models import Bill
from src.financial.budgets.models import Budget
from src.financial.debt.models import Debt
from src.financial.engine.financial_snapshot_builder import (
    build_financial_snapshot as build_snapshot_facts,
)
from src.financial.expenses.models import Expense
from src.financial.goals.models import Goal
from src.financial.income.models import Income
from src.financial.insights.insight_engine import generate_insights
from src.financial.recommendations.service import generate_recommendations


def build_financial_snapshot(
    user_id: int,
    income_entries: list[Income],
    expenses: list[Expense],
    budgets: list[Budget],
    accounts: list[Account],
    goals: list[Goal],
    debts: list[Debt],
    bills: list[Bill] | None = None,
    current_day: int | None = None,
) -> dict:
    """
    Build a complete financial snapshot, including insights and
    recommendations, for the coach/CLI/history dict-based consumers.

    Delegates all financial-fact computation to
    financial_snapshot_builder.build_financial_snapshot() -- the
    canonical, ADR-002-sanctioned source -- rather than recomputing it
    independently, and reuses the same rule-engine adapter the public
    /recommendations API uses rather than hand-building a second
    snapshot dict for the rule engine.
    """

    financial_snapshot = build_snapshot_facts(
        income_entries=income_entries,
        expenses=expenses,
        budgets=budgets,
        accounts=accounts,
        goals=goals,
        debts=debts,
        bills=bills,
        current_day=current_day,
    )

    insights = generate_insights(
        {
            "net_cash_flow": financial_snapshot.net_cash_flow,
            "total_debt": financial_snapshot.total_debt,
            "total_account_balance": financial_snapshot.total_account_balance,
            "health_score": financial_snapshot.health_score,
        }
    )

    rule_snapshot = build_rule_snapshot(financial_snapshot)

    recommendations = generate_recommendations(user_id, rule_snapshot)

    snapshot = financial_snapshot.to_dict()

    snapshot["insights"] = insights
    snapshot["recommendations"] = [
        recommendation.to_dict() for recommendation in recommendations
    ]

    return snapshot
