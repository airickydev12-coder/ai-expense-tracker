from src.financial.budgets.models import Budget
from src.financial.shared.categories import ExpenseCategory
from src.presentation import views


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
    assert "$  500.00" in output
    assert "Transportation" in output
    assert "$  300.00" in output


def test_display_current_budgets_when_empty(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        views,
        "get_budgets",
        lambda: [],
    )

    views.display_current_budgets()

    output = capsys.readouterr().out

    assert (
        "No budgets have been created yet."
        in output
    )


def test_show_menu_includes_financial_snapshot(
    capsys,
):
    views.show_menu()

    output = capsys.readouterr().out

    assert "9. View Financial Snapshot" in output
    assert "10. Exit" in output


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
        "accounts": [
            {
                "id": 1,
                "name": "Checking",
            }
        ],
        "goals": [
            {
                "id": 1,
                "name": "Emergency Fund",
            }
        ],
        "debts": [
            {
                "id": 1,
                "name": "Credit Card",
            }
        ],
        "bills": [
            {
                "id": 1,
                "name": "Electric",
            }
        ],
        "recommendations": [
            {
                "priority": "HIGH",
                "category": "Debt",
                "title": "High Interest Debt",
                "message": (
                    "Your credit card has a "
                    "high interest rate."
                ),
                "action": (
                    "Prioritize paying down "
                    "the credit card."
                ),
            }
        ],
    }

    views.display_financial_snapshot(snapshot)

    output = capsys.readouterr().out

    assert "Financial Snapshot" in output
    assert "Total Income:" in output
    assert "$5000.00" in output
    assert "Net Cash Flow:" in output
    assert "$3500.00" in output
    assert "Financial Health:" in output
    assert "85 (Excellent)" in output
    assert "Accounts:" in output
    assert "Goals:" in output
    assert "Debts:" in output
    assert "Bills:" in output
    assert "High Interest Debt" in output
    assert "Prioritize paying down" in output


def test_display_financial_snapshot_without_recommendations(
    capsys,
):
    snapshot = {
        "total_income": 0,
        "total_expenses": 0,
        "net_cash_flow": 0,
        "total_account_balance": 0,
        "total_goal_progress": 0,
        "total_debt": 0,
        "net_worth": 0,
        "health_score": 0,
        "health_status": "Critical",
        "accounts": [],
        "goals": [],
        "debts": [],
        "bills": [],
        "recommendations": [],
    }

    views.display_financial_snapshot(snapshot)

    output = capsys.readouterr().out

    assert "No recommendations are available." in output