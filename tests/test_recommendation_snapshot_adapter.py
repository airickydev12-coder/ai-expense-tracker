"""Tests for the recommendation snapshot adapter."""

from decimal import Decimal

from src.financial.application.financial_snapshot import (
    FinancialSnapshot,
)
from src.financial.application.recommendation_snapshot_adapter import (
    build_rule_snapshot,
)


def test_build_rule_snapshot_maps_snapshot_fields() -> None:
    """FinancialSnapshot fields are mapped correctly."""

    snapshot = FinancialSnapshot(
        total_income=Decimal("1000.00"),
        total_expenses=Decimal("250.00"),
        net_cash_flow=Decimal("750.00"),
        average_expense=Decimal("50.00"),
        highest_expense=None,
        lowest_expense=None,
        category_totals={
            "Food": Decimal("150.00"),
        },
        budget_count=2,
        goal_count=1,
        budget_report=[],
        total_account_balance=Decimal("5000.00"),
        total_goal_progress=Decimal("1000.00"),
        total_debt=Decimal("500.00"),
        net_worth=Decimal("5500.00"),
        accounts=[],
        goals=[],
        debts=[],
        bills=[],
        current_day=15,
        health_score=82,
        health_status="Good",
    )

    rule_snapshot = build_rule_snapshot(snapshot)

    assert rule_snapshot["total_expenses"] == Decimal("250.00")
    assert rule_snapshot["average_expense"] == Decimal("50.00")
    assert rule_snapshot["category_totals"] == {
        "Food": Decimal("150.00"),
    }
    assert rule_snapshot["health_score"] == 82
    assert rule_snapshot["health_status"] == "Good"
    assert rule_snapshot["largest_expense"] is None


def test_build_rule_snapshot_includes_financial_domains() -> None:
    """Canonical financial domains are included in the rule snapshot."""

    snapshot = FinancialSnapshot(
        total_income=Decimal("0"),
        total_expenses=Decimal("0"),
        net_cash_flow=Decimal("0"),
        average_expense=Decimal("0"),
        highest_expense=None,
        lowest_expense=None,
        category_totals={},
        budget_count=0,
        goal_count=0,
        budget_report=[],
        total_account_balance=Decimal("0"),
        total_goal_progress=Decimal("0"),
        total_debt=Decimal("0"),
        net_worth=Decimal("0"),
        accounts=[],
        goals=[],
        debts=[],
        bills=[],
        current_day=15,
        health_score=65,
        health_status="Fair",
    )

    expected_keys = {
        "average_expense",
        "bills",
        "budget_report",
        "category_totals",
        "current_day",
        "debts",
        "goals",
        "health_score",
        "health_status",
        "largest_expense",
        "net_cash_flow",
        "net_worth",
        "total_account_balance",
        "total_debt",
        "total_expenses",
        "total_goal_progress",
        "total_income",
    }

    rule_snapshot = build_rule_snapshot(snapshot)

    assert rule_snapshot["goals"] == []
    assert rule_snapshot["bills"] == []
    assert rule_snapshot["debts"] == []
    assert rule_snapshot["budget_report"] == []

    assert rule_snapshot["total_income"] == Decimal("0")
    assert rule_snapshot["total_account_balance"] == Decimal("0")
    assert rule_snapshot["total_debt"] == Decimal("0")
    assert rule_snapshot["total_goal_progress"] == Decimal("0")
    assert rule_snapshot["net_cash_flow"] == Decimal("0")
    assert rule_snapshot["net_worth"] == Decimal("0")

    assert rule_snapshot["current_day"] == 15
    assert set(rule_snapshot.keys()) == expected_keys
