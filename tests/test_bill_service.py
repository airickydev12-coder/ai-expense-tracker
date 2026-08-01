from decimal import Decimal


from src.financial.bills.service import (
    add_bill,
    bills,
    delete_bill,
    get_bill_by_id,
    get_bills,
    get_next_bill_id,
    load_bills,
    mark_bill_paid,
    mark_bill_unpaid,
    update_bill,
)


def setup_function():
    """Clear bill state before every test."""
    bills.clear()


def test_add_bill(tmp_path):
    file_path = tmp_path / "bills.json"

    bill = add_bill(
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        file_path=file_path,
    )

    assert bill.id == 1
    assert bill.name == "Electric"
    assert bill.amount == 125
    assert bill.due_day == 15
    assert bill.is_paid is False
    assert file_path.exists()


def test_add_multiple_bills_assigns_unique_ids(
    tmp_path,
):
    file_path = tmp_path / "bills.json"

    first_bill = add_bill(
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        file_path=file_path,
    )

    second_bill = add_bill(
        name="Internet",
        amount=Decimal("80.00"),
        due_day=20,
        file_path=file_path,
    )

    assert first_bill.id == 1
    assert second_bill.id == 2
    assert get_next_bill_id() == 3


def test_get_bills_returns_copy(
    tmp_path,
):
    file_path = tmp_path / "bills.json"

    add_bill(
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        file_path=file_path,
    )

    returned_bills = get_bills()
    returned_bills.clear()

    assert len(bills) == 1


def test_get_bill_by_id(tmp_path):
    file_path = tmp_path / "bills.json"

    created_bill = add_bill(
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        file_path=file_path,
    )

    assert get_bill_by_id(created_bill.id) == created_bill


def test_get_bill_by_id_returns_none():
    assert get_bill_by_id(999) is None


def test_update_bill(tmp_path):
    file_path = tmp_path / "bills.json"

    bill = add_bill(
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        file_path=file_path,
    )

    updated_bill = update_bill(
        bill_id=bill.id,
        name="Electric Utility",
        amount=Decimal("140.00"),
        due_day=16,
        file_path=file_path,
    )

    assert updated_bill is not None
    assert updated_bill.name == "Electric Utility"
    assert updated_bill.amount == Decimal("140.00")
    assert updated_bill.due_day == 16
    assert updated_bill.is_paid is False


def test_update_bill_preserves_unchanged_fields(
    tmp_path,
):
    file_path = tmp_path / "bills.json"

    bill = add_bill(
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        file_path=file_path,
    )

    updated_bill = update_bill(
        bill_id=bill.id,
        amount=Decimal("130.00"),
        file_path=file_path,
    )

    assert updated_bill is not None
    assert updated_bill.name == "Electric"
    assert updated_bill.amount == Decimal("130.00")
    assert updated_bill.due_day == 15
    assert updated_bill.is_paid is False


def test_update_bill_returns_none_when_missing(
    tmp_path,
):
    file_path = tmp_path / "bills.json"

    assert (
        update_bill(
            bill_id=999,
            name="Missing",
            file_path=file_path,
        )
        is None
    )


def test_mark_bill_paid(tmp_path):
    file_path = tmp_path / "bills.json"

    bill = add_bill(
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        file_path=file_path,
    )

    updated_bill = mark_bill_paid(
        bill.id,
        file_path=file_path,
    )

    assert updated_bill is not None
    assert updated_bill.is_paid is True


def test_mark_bill_unpaid(tmp_path):
    file_path = tmp_path / "bills.json"

    bill = add_bill(
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        is_paid=True,
        file_path=file_path,
    )

    updated_bill = mark_bill_unpaid(
        bill.id,
        file_path=file_path,
    )

    assert updated_bill is not None
    assert updated_bill.is_paid is False


def test_delete_bill(tmp_path):
    file_path = tmp_path / "bills.json"

    bill = add_bill(
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        file_path=file_path,
    )

    deleted_bill = delete_bill(
        bill.id,
        file_path=file_path,
    )

    assert deleted_bill == bill
    assert get_bills() == []


def test_delete_bill_returns_none_when_missing(
    tmp_path,
):
    file_path = tmp_path / "bills.json"

    assert (
        delete_bill(
            999,
            file_path=file_path,
        )
        is None
    )


def test_load_bills_restores_saved_bills(
    tmp_path,
):
    file_path = tmp_path / "bills.json"

    add_bill(
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        file_path=file_path,
    )

    bills.clear()

    load_bills(file_path)

    loaded_bills = get_bills()

    assert len(loaded_bills) == 1
    assert loaded_bills[0].name == "Electric"
    assert loaded_bills[0].amount == 125
