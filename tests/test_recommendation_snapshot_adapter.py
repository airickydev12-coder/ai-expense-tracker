from src.financial.application.financial_snapshot_service import (
    FinancialSnapshot,
)
from src.financial.application.recommendation_snapshot_adapter import (
    build_rule_snapshot,
)


def test_build_rule_snapshot_maps_snapshot_fields():
    """FinancialSnapshot fields are mapped correctly."""

    snapshot = FinancialSnapshot(
        total_expenses=250.0,
        average_expense=50.0,
        highest_expense=None,
        lowest_expense=None,
        category_totals={"Food": 150.0},
        budget_count=2,
        goal_count=1,
        health_score=82,
        health_status="Good",
    )

    rule_snapshot = build_rule_snapshot(snapshot)

    assert rule_snapshot["total_expenses"] == 250.0
    assert rule_snapshot["average_expense"] == 50.0
    assert rule_snapshot["category_totals"] == {"Food": 150.0}
    assert rule_snapshot["health_score"] == 82
    assert rule_snapshot["health_status"] == "Good"
    assert rule_snapshot["largest_expense"] is None


def test_build_rule_snapshot_includes_future_placeholders():
    """Future financial domains are initialized."""

    snapshot = FinancialSnapshot(
        total_expenses=0.0,
        average_expense=0.0,
        highest_expense=None,
        lowest_expense=None,
        category_totals={},
        budget_count=0,
        goal_count=0,
        health_score=0,
        health_status="Poor",
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
    assert rule_snapshot["budget_report"] == {}
    assert rule_snapshot["total_income"] == 0.0
    assert rule_snapshot["total_account_balance"] == 0.0
    assert rule_snapshot["total_debt"] == 0.0
    assert rule_snapshot["total_goal_progress"] == 0.0
    assert rule_snapshot["net_cash_flow"] == 0.0
    assert rule_snapshot["net_worth"] == 0.0
    assert set(rule_snapshot.keys()) == expected_keys
