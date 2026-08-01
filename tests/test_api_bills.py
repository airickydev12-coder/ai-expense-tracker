"""Tests for the bill API endpoints."""

from fastapi.testclient import TestClient

from src.api.main import app
from src.financial.bills.service import bills

client = TestClient(app)


def setup_function() -> None:
    """Reset in-memory bills before each test."""
    bills.clear()


def test_list_bills_returns_empty_list() -> None:
    response = client.get("/bills")

    assert response.status_code == 200
    assert response.json() == []


def test_create_bill() -> None:
    response = client.post(
        "/bills",
        json={
            "name": "Electric",
            "amount": 125.00,
            "due_day": 15,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Electric",
        "amount": 125.0,
        "due_day": 15,
        "is_paid": False,
    }


def test_get_bill_by_id() -> None:
    created = client.post(
        "/bills",
        json={"name": "Electric", "amount": 125.00, "due_day": 15},
    ).json()

    response = client.get(f"/bills/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_bill_returns_404_when_missing() -> None:
    response = client.get("/bills/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Bill with ID 999 was not found."}


def test_update_bill() -> None:
    created = client.post(
        "/bills",
        json={"name": "Electric", "amount": 125.00, "due_day": 15},
    ).json()

    response = client.put(
        f"/bills/{created['id']}",
        json={"amount": 140.00},
    )

    assert response.status_code == 200
    assert response.json()["amount"] == 140.0


def test_update_bill_returns_404_when_missing() -> None:
    response = client.put("/bills/999", json={"amount": 140.00})

    assert response.status_code == 404


def test_pay_bill() -> None:
    created = client.post(
        "/bills",
        json={"name": "Electric", "amount": 125.00, "due_day": 15},
    ).json()

    response = client.patch(f"/bills/{created['id']}/pay")

    assert response.status_code == 200
    assert response.json()["is_paid"] is True


def test_pay_bill_returns_404_when_missing() -> None:
    response = client.patch("/bills/999/pay")

    assert response.status_code == 404


def test_unpay_bill() -> None:
    created = client.post(
        "/bills",
        json={"name": "Electric", "amount": 125.00, "due_day": 15, "is_paid": True},
    ).json()

    response = client.patch(f"/bills/{created['id']}/unpay")

    assert response.status_code == 200
    assert response.json()["is_paid"] is False


def test_unpay_bill_returns_404_when_missing() -> None:
    response = client.patch("/bills/999/unpay")

    assert response.status_code == 404


def test_delete_bill() -> None:
    created = client.post(
        "/bills",
        json={"name": "Electric", "amount": 125.00, "due_day": 15},
    ).json()

    response = client.delete(f"/bills/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created
    assert client.get("/bills").json() == []


def test_delete_bill_returns_404_when_missing() -> None:
    response = client.delete("/bills/999")

    assert response.status_code == 404
