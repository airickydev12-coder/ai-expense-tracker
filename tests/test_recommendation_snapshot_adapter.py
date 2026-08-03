"""Tests for the recommendation snapshot adapter."""

from decimal import Decimal

from src.financial.application.financial_snapshot import (
    FinancialSnapshot,
)
from src.financial.application.recommendation_snapshot_adapter import (
    build_rule_snapshot,
)
from src.financial.bills.models import Bill
from src.financial.debt.models import Debt
from src.financial.expenses.models import Expense
from src.financial.goals.models import Goal
from src.financial.recommendations.service import generate_recommendations
from src.financial.shared.categories import ExpenseCategory


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


def test_build_rule_snapshot_converts_domain_objects_to_dicts() -> None:
    """
    Regression test: goals/debts/bills/largest_expense must be plain
    dicts, not raw model instances, since rules access them by
    subscript (e.g. bill["is_paid"]) rather than attribute access.
    """

    snapshot = FinancialSnapshot(
        total_income=Decimal("4000.00"),
        total_expenses=Decimal("350.00"),
        net_cash_flow=Decimal("3650.00"),
        average_expense=Decimal("50.00"),
        highest_expense=Expense(
            id=1,
            name="Car Repair",
            category=ExpenseCategory.MAINTENANCE,
            amount=Decimal("300.00"),
        ),
        lowest_expense=None,
        category_totals={
            "Maintenance": Decimal("300.00"),
        },
        budget_count=0,
        goal_count=1,
        budget_report=[],
        total_account_balance=Decimal("2000.00"),
        total_goal_progress=Decimal("200.00"),
        total_debt=Decimal("5000.00"),
        net_worth=Decimal("-2800.00"),
        accounts=[],
        goals=[
            Goal(
                id=1,
                name="Emergency Fund",
                target_amount=Decimal("1000.00"),
                current_amount=Decimal("200.00"),
            )
        ],
        debts=[
            Debt(
                id=1,
                name="Credit Card",
                balance=Decimal("5000.00"),
                interest_rate=0.20,
                minimum_payment=Decimal("100.00"),
            )
        ],
        bills=[
            Bill(
                id=1,
                name="Electric Bill",
                amount=Decimal("120.00"),
                due_day=16,
                is_paid=False,
            )
        ],
        current_day=15,
        health_score=55,
        health_status="Fair",
    )

    rule_snapshot = build_rule_snapshot(snapshot)

    assert rule_snapshot["largest_expense"]["amount"] == Decimal("300.00")
    assert rule_snapshot["goals"][0]["current_amount"] == Decimal("200.00")
    assert rule_snapshot["debts"][0]["balance"] == Decimal("5000.00")
    assert rule_snapshot["bills"][0]["is_paid"] is False

    # Previously raised TypeError: '<Model>' object is not subscriptable,
    # since rules read these fields via bill["is_paid"], debt["balance"],
    # etc. Running the real rule engine end-to-end proves the fix holds,
    # not just that build_rule_snapshot() returns the right shape.
    recommendations = generate_recommendations(1, rule_snapshot)

    titles = {recommendation.title for recommendation in recommendations}

    assert "Bill Due Soon" in titles
    assert "Expense Spike Detected" in titles
