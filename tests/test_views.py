from datetime import datetime, timedelta, timezone

from src.financial.budgets.models import Budget
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.recommendations.history import RecommendationRecord
from src.financial.recommendations.status import RecommendationStatus
from src.financial.shared.categories import ExpenseCategory
from src.presentation import views


def build_history() -> list[FinancialSnapshotRecord]:
    """Create financial history for view tests."""
    now = datetime.now(timezone.utc)

    return [
        FinancialSnapshotRecord(
            timestamp=now - timedelta(days=30),
            total_income=4000,
            total_expenses=2000,
            net_cash_flow=2000,
            total_account_balance=1500,
            total_goal_progress=1000,
            total_debt=2000,
            net_worth=500,
            health_score=60,
            health_status="Fair",
        ),
        FinancialSnapshotRecord(
            timestamp=now,
            total_income=5000,
            total_expenses=1800,
            net_cash_flow=3200,
            total_account_balance=2500,
            total_goal_progress=2000,
            total_debt=1500,
            net_worth=3000,
            health_score=80,
            health_status="Good",
        ),
    ]


def test_display_current_budgets(
    monkeypatch,
    capsys,
):
    budgets = [
        Budget(
            category=ExpenseCategory.FOOD,
            limit=500,
        ),
        Budget(
            category=ExpenseCategory.TRANSPORTATION,
            limit=300,
        ),
    ]

    monkeypatch.setattr(
        views,
        "get_budgets",
        lambda: budgets,
    )

    views.display_current_budgets()

    output = capsys.readouterr().out

    assert "Current Budgets" in output
    assert "Food" in output
    assert "Transportation" in output


def test_show_menu_includes_financial_trends(
    capsys,
):
    views.show_menu()

    output = capsys.readouterr().out

    assert "9. View Financial Snapshot" in output
    assert "10. Manage Recommendations" in output
    assert "11. View Financial Trends" in output
    assert "12. Exit" in output


def test_recommendation_management_menu(
    capsys,
):
    views.display_recommendation_management_menu()

    output = capsys.readouterr().out

    assert "View Active Recommendations" in output
    assert "Mark Recommendation Completed" in output
    assert "Suppress Recommendation" in output
    assert "7. Back" in output


def test_display_recommendations(
    capsys,
):
    recommendations = [
        {
            "key": "debt:high_interest_debt",
            "priority": "HIGH",
            "category": "Debt",
            "title": "High Interest Debt",
            "message": "You have high-interest debt.",
            "action": "Prioritize repayment.",
        }
    ]

    views.display_recommendations(
        recommendations
    )

    output = capsys.readouterr().out

    assert "Active Recommendations" in output
    assert "High Interest Debt" in output
    assert "debt:high_interest_debt" in output
    assert "Prioritize repayment" in output


def test_display_recommendations_when_empty(
    capsys,
):
    views.display_recommendations([])

    output = capsys.readouterr().out

    assert (
        "No active recommendations are available."
        in output
    )


def test_display_recommendation_history(
    capsys,
):
    timestamp = datetime.now(timezone.utc)

    records = [
        RecommendationRecord(
            recommendation_key=(
                "debt:high_interest_debt"
            ),
            status=RecommendationStatus.COMPLETED,
            created_at=timestamp,
            updated_at=timestamp,
            note="Debt paid off.",
        )
    ]

    views.display_recommendation_history(
        records
    )

    output = capsys.readouterr().out

    assert "Recommendation History" in output
    assert "COMPLETED" in output
    assert "debt:high_interest_debt" in output
    assert "Debt paid off." in output


def test_display_recommendation_history_empty(
    capsys,
):
    views.display_recommendation_history([])

    output = capsys.readouterr().out

    assert (
        "No recommendation history is available."
        in output
    )


def test_display_financial_snapshot(
    capsys,
):
    snapshot = {
        "total_income": 5000,
        "total_expenses": 1500,
        "net_cash_flow": 3500,
        "total_account_balance": 2000,
        "total_goal_progress": 2500,
        "total_debt": 1000,
        "net_worth": 3500,
        "health_score": 85,
        "health_status": "Excellent",
        "accounts": [{}],
        "goals": [{}],
        "debts": [{}],
        "bills": [{}],
        "recommendations": [
            {
                "priority": "HIGH",
                "category": "Debt",
                "title": "High Interest Debt",
                "message": "Debt detected.",
                "action": "Prioritize repayment.",
            }
        ],
    }

    views.display_financial_snapshot(snapshot)

    output = capsys.readouterr().out

    assert "Financial Snapshot" in output
    assert "$5000.00" in output
    assert "$3500.00" in output
    assert "85 (Excellent)" in output
    assert "High Interest Debt" in output


def test_display_financial_trends(
    capsys,
):
    views.display_financial_trends(
        build_history()
    )

    output = capsys.readouterr().out

    assert "Financial Trends" in output
    assert "Snapshots Recorded:" in output
    assert "2" in output
    assert "Net Worth Change:" in output
    assert "+$2,500.00" in output
    assert "Cash Flow Change:" in output
    assert "+$1,200.00" in output
    assert "Income Change:" in output
    assert "+$1,000.00" in output
    assert "Expense Change:" in output
    assert "-$200.00" in output
    assert "Health Score Change:" in output
    assert "+20" in output


def test_display_financial_trends_without_history(
    capsys,
):
    views.display_financial_trends([])

    output = capsys.readouterr().out

    assert (
        "No financial snapshots have been recorded."
        in output
    )


def test_display_financial_trends_with_one_snapshot(
    capsys,
):
    history = [build_history()[0]]

    views.display_financial_trends(history)

    output = capsys.readouterr().out

    assert "Snapshots Recorded:" in output
    assert (
        "Record at least two snapshots"
        in output
    )

def test_display_financial_trends_includes_intelligence(
    capsys,
):
    views.display_financial_trends(
        build_history()
    )

    output = capsys.readouterr().out

    assert "Trend Intelligence" in output
    assert "Overall Momentum:      Positive" in output
    assert "Net Worth Trend:       Improving" in output
    assert "Cash Flow Trend:       Improving" in output
    assert "Income Trend:          Improving" in output
    assert "Expense Trend:         Improving" in output
    assert "Health Trend:          Improving" in output