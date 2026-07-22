"""Tests for the canonical financial snapshot builder."""

from src.financial.application.financial_snapshot import (
    FinancialSnapshot,
)
from src.financial.engine.financial_snapshot_builder import (
    build_financial_snapshot,
)
from decimal import Decimal


def test_build_empty_financial_snapshot() -> None:
    """Build a valid snapshot when no financial data exists."""

    snapshot = build_financial_snapshot(
        income_entries=[],
        expenses=[],
        budgets=[],
        accounts=[],
        goals=[],
        debts=[],
        bills=[],
        current_day=15,
    )

    assert isinstance(snapshot, FinancialSnapshot)

    assert snapshot.total_income == 0
    assert snapshot.total_expenses == 0
    assert snapshot.net_cash_flow == 0

    assert snapshot.average_expense == 0
    assert snapshot.highest_expense is None
    assert snapshot.lowest_expense is None
    assert snapshot.category_totals == {}

    assert snapshot.budget_count == 0
    assert snapshot.goal_count == 0
    assert snapshot.budget_report == []

    assert snapshot.total_account_balance == 0
    assert snapshot.total_goal_progress == 0
    assert snapshot.total_debt == 0
    assert snapshot.net_worth == 0

    assert snapshot.accounts == []
    assert snapshot.goals == []
    assert snapshot.debts == []
    assert snapshot.bills == []

    assert snapshot.current_day == 15

    assert isinstance(snapshot.health_score, int)
    assert isinstance(snapshot.health_status, str)


def test_snapshot_dictionary_excludes_decision_outputs() -> None:
    """Exclude recommendations and insights from financial state."""

    snapshot = build_financial_snapshot(
        income_entries=[],
        expenses=[],
        budgets=[],
        accounts=[],
        goals=[],
        debts=[],
        bills=[],
        current_day=15,
    )

    snapshot_data = snapshot.to_dict()

    assert "insights" not in snapshot_data
    assert "recommendations" not in snapshot_data

    assert snapshot_data["total_income"] == 0
    assert snapshot_data["total_expenses"] == 0
    assert snapshot_data["current_day"] == 15
