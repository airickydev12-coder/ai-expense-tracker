from decimal import Decimal

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from src.api.main import app
from src.financial.expenses import service as expense_service
from src.financial.expenses.models import Expense
from src.financial.shared.categories import ExpenseCategory

client = TestClient(app)


def test_category_totals_empty(monkeypatch: MonkeyPatch) -> None:
    """Return an empty list when no expenses exist."""
    monkeypatch.setattr(expense_service, "expenses", [])

    response = client.get("/expenses/category-totals")

    assert response.status_code == 200
    assert response.json() == []


def test_category_totals_returns_grouped_totals(
    monkeypatch: MonkeyPatch,
) -> None:
    """Return spending totals grouped by category."""
    test_expenses = [
        Expense(
            id=1,
            name="Coffee",
            category=ExpenseCategory.FOOD,
            amount=Decimal("5.00"),
        ),
        Expense(
            id=2,
            name="Lunch",
            category=ExpenseCategory.FOOD,
            amount=Decimal("15.00"),
        ),
        Expense(
            id=3,
            name="Gas",
            category=ExpenseCategory.TRANSPORTATION,
            amount=Decimal("40.00"),
        ),
    ]

    monkeypatch.setattr(expense_service, "expenses", test_expenses)

    response = client.get("/expenses/category-totals")

    assert response.status_code == 200
    assert response.json() == [
        {
            "category": "Food",
            "total": 20.0,
        },
        {
            "category": "Transportation",
            "total": 40.0,
        },
    ]


def test_expense_statistics_empty(monkeypatch: MonkeyPatch) -> None:
    """Return zeroed statistics when no expenses exist."""
    monkeypatch.setattr(expense_service, "expenses", [])

    response = client.get("/expenses/statistics")

    assert response.status_code == 200
    assert response.json() == {
        "total": 0.0,
        "average": 0.0,
        "highest": None,
        "lowest": None,
    }


def test_expense_statistics_returns_summary(
    monkeypatch: MonkeyPatch,
) -> None:
    """Return total, average, highest, and lowest expenses."""
    test_expenses = [
        Expense(
            id=1,
            name="Coffee",
            category=ExpenseCategory.FOOD,
            amount=Decimal("5.00"),
        ),
        Expense(
            id=2,
            name="Rent",
            category=ExpenseCategory.HOUSING,
            amount=Decimal("1200.00"),
        ),
        Expense(
            id=3,
            name="Gas",
            category=ExpenseCategory.TRANSPORTATION,
            amount=Decimal("45.00"),
        ),
    ]

    monkeypatch.setattr(expense_service, "expenses", test_expenses)

    response = client.get("/expenses/statistics")

    assert response.status_code == 200

    assert response.json() == {
        "total": 1250.0,
        "average": 416.67,
        "highest": {
            "id": 2,
            "name": "Rent",
            "category": "Housing",
            "amount": 1200.0,
        },
        "lowest": {
            "id": 1,
            "name": "Coffee",
            "category": "Food",
            "amount": 5.0,
        },
    }
