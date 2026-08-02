"""Tests for the expense API endpoints."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.schemas.expenses import ExpenseCreateRequest, ExpenseUpdateRequest
from src.core.exceptions import ExternalServiceError
from src.financial.expenses import categorization as expense_categorization
from src.financial.expenses import service as expense_service
from src.financial.expenses.models import Expense
from src.financial.shared.categories import ExpenseCategory

client = TestClient(app)


def test_list_expenses_returns_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """The endpoint should return an empty list when no expenses exist."""
    monkeypatch.setattr(expense_service, "expenses", [])
    response = client.get("/expenses")
    assert response.status_code == 200
    assert response.json() == []


def test_list_expenses_returns_serialized_expenses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The endpoint should serialize existing domain expenses."""
    test_expenses = [
        Expense(
            id=1,
            name="Coffee",
            category=ExpenseCategory.FOOD,
            amount=Decimal("5.25"),
        )
    ]
    monkeypatch.setattr(expense_service, "expenses", test_expenses)
    response = client.get("/expenses")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Coffee", "category": "Food", "amount": 5.25}
    ]


def test_create_expense_returns_created_expense(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Creating an expense should return HTTP 201."""
    created = Expense(
        id=1,
        name="Coffee",
        category=ExpenseCategory.FOOD,
        amount=Decimal("5.25"),
    )

    def fake_add_expense(
        name: str,
        category: ExpenseCategory,
        amount: Decimal,
    ) -> Expense:
        assert name == "Coffee"
        assert category == ExpenseCategory.FOOD
        assert amount == Decimal("5.25")
        return created

    monkeypatch.setattr(expense_service, "add_expense", fake_add_expense)
    request = ExpenseCreateRequest(
        name="Coffee",
        category=ExpenseCategory.FOOD,
        amount=Decimal("5.25"),
    )
    response = client.post("/expenses", json=request.model_dump(mode="json"))
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Coffee",
        "category": "Food",
        "amount": 5.25,
    }


def test_create_expense_rejects_negative_amount(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Negative amounts should fail before the service is called."""

    def fail_if_called(
        name: str,
        category: ExpenseCategory,
        amount: Decimal,
    ) -> Expense:
        pytest.fail("add_expense should not be called for invalid input")

    monkeypatch.setattr(expense_service, "add_expense", fail_if_called)
    response = client.post(
        "/expenses",
        json={"name": "Coffee", "category": "Food", "amount": -1},
    )
    assert response.status_code == 422


def test_get_expense_returns_serialized_expense(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An existing expense should be returned by ID."""
    existing_expense = Expense(
        id=7,
        name="Groceries",
        category=ExpenseCategory.FOOD,
        amount=Decimal("84.50"),
    )

    def fake_get_expense_by_id(expense_id: int) -> Expense | None:
        assert expense_id == 7
        return existing_expense

    monkeypatch.setattr(expense_service, "get_expense_by_id", fake_get_expense_by_id)
    response = client.get("/expenses/7")
    assert response.status_code == 200
    assert response.json() == {
        "id": 7,
        "name": "Groceries",
        "category": "Food",
        "amount": 84.50,
    }


def test_get_expense_returns_404_when_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing expense should return HTTP 404."""

    def fake_get_expense_by_id(expense_id: int) -> Expense | None:
        assert expense_id == 999
        return None

    monkeypatch.setattr(expense_service, "get_expense_by_id", fake_get_expense_by_id)
    response = client.get("/expenses/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Expense with ID 999 was not found."}


def test_update_expense_returns_updated_expense(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Updating an expense should return the updated expense."""
    updated = Expense(
        id=5,
        name="Lunch",
        category=ExpenseCategory.FOOD,
        amount=Decimal("18.75"),
    )

    def fake_update_expense(
        expense_id: int,
        name: str | None = None,
        category: ExpenseCategory | None = None,
        amount: Decimal | None = None,
    ) -> Expense | None:
        assert expense_id == 5
        assert name == "Lunch"
        assert category == ExpenseCategory.FOOD
        assert amount == Decimal("18.75")
        return updated

    monkeypatch.setattr(expense_service, "update_expense", fake_update_expense)
    request = ExpenseUpdateRequest(
        name="Lunch",
        category=ExpenseCategory.FOOD,
        amount=Decimal("18.75"),
    )
    response = client.put("/expenses/5", json=request.model_dump(mode="json"))
    assert response.status_code == 200
    assert response.json() == {
        "id": 5,
        "name": "Lunch",
        "category": "Food",
        "amount": 18.75,
    }


def test_update_expense_returns_404(monkeypatch: pytest.MonkeyPatch) -> None:
    """Updating a missing expense should return HTTP 404."""
    monkeypatch.setattr(
        expense_service,
        "update_expense",
        lambda *args, **kwargs: None,
    )
    response = client.put("/expenses/999", json={"name": "Coffee"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Expense with ID 999 was not found."}


def test_update_expense_requires_at_least_one_field() -> None:
    """An empty update request should return HTTP 400."""
    response = client.put("/expenses/1", json={})
    assert response.status_code == 400
    assert response.json() == {"detail": "At least one field must be provided."}


def test_update_expense_rejects_negative_amount() -> None:
    """Negative amounts should fail validation."""
    response = client.put("/expenses/1", json={"amount": -5})
    assert response.status_code == 422


def test_delete_expense_returns_deleted_expense(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deleting an existing expense should return the removed expense."""
    deleted = Expense(
        id=8,
        name="Parking",
        category=ExpenseCategory.TRANSPORTATION,
        amount=Decimal("12.00"),
    )

    def fake_delete_expense(expense_id: int) -> Expense | None:
        assert expense_id == 8
        return deleted

    monkeypatch.setattr(expense_service, "delete_expense", fake_delete_expense)
    response = client.delete("/expenses/8")
    assert response.status_code == 200
    assert response.json() == {
        "id": 8,
        "name": "Parking",
        "category": "Transportation",
        "amount": 12.00,
    }


def test_delete_expense_returns_404_when_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deleting a missing expense should return HTTP 404."""

    def fake_delete_expense(expense_id: int) -> Expense | None:
        assert expense_id == 999
        return None

    monkeypatch.setattr(expense_service, "delete_expense", fake_delete_expense)
    response = client.delete("/expenses/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Expense with ID 999 was not found."}


def test_suggest_expense_category_returns_suggested_category(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A valid name should return the suggested category."""

    def fake_suggest_category(name: str) -> ExpenseCategory:
        assert name == "Trader Joe's"
        return ExpenseCategory.FOOD

    monkeypatch.setattr(
        expense_categorization, "suggest_category", fake_suggest_category
    )
    response = client.post(
        "/expenses/suggest-category", json={"name": "Trader Joe's"}
    )
    assert response.status_code == 200
    assert response.json() == {"category": "Food"}


def test_suggest_expense_category_rejects_empty_name() -> None:
    """An empty name should fail validation before the service is called."""
    response = client.post("/expenses/suggest-category", json={"name": ""})
    assert response.status_code == 422


def test_suggest_expense_category_returns_502_on_external_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An external-service failure should surface as HTTP 502."""

    def fake_suggest_category(name: str) -> ExpenseCategory:
        raise ExternalServiceError("Category suggestion is unavailable: boom")

    monkeypatch.setattr(
        expense_categorization, "suggest_category", fake_suggest_category
    )
    response = client.post("/expenses/suggest-category", json={"name": "Coffee"})
    assert response.status_code == 502
    assert response.json() == {
        "detail": "Category suggestion is unavailable: boom"
    }
