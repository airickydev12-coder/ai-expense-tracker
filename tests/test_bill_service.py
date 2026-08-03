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
from src.financial.users.repository import create_user

USER_ID = 1


def setup_function():
    """Clear bill state before every test."""
    bills.clear()


def _create_user(db_path, username: str = "alice") -> None:
    """Insert a throwaway user row so bills' FK constraint is satisfied."""
    create_user(username, f"{username}@example.com", "hash", db_path)


def test_add_bill(tmp_path):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    bill = add_bill(
        user_id=USER_ID,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        db_path=db_path,
    )

    assert bill.id == 1
    assert bill.name == "Electric"
    assert bill.amount == 125
    assert bill.due_day == 15
    assert bill.is_paid is False
    assert db_path.exists()


def test_add_multiple_bills_assigns_unique_ids(
    tmp_path,
):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    first_bill = add_bill(
        user_id=USER_ID,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        db_path=db_path,
    )

    second_bill = add_bill(
        user_id=USER_ID,
        name="Internet",
        amount=Decimal("80.00"),
        due_day=20,
        db_path=db_path,
    )

    assert first_bill.id == 1
    assert second_bill.id == 2
    assert get_next_bill_id(USER_ID) == 3


def test_get_bills_returns_copy(
    tmp_path,
):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    add_bill(
        user_id=USER_ID,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        db_path=db_path,
    )

    returned_bills = get_bills(USER_ID, db_path=db_path)
    returned_bills.clear()

    assert len(bills[USER_ID]) == 1


def test_get_bill_by_id(tmp_path):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    created_bill = add_bill(
        user_id=USER_ID,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        db_path=db_path,
    )

    assert get_bill_by_id(USER_ID, created_bill.id, db_path=db_path) == created_bill


def test_get_bill_by_id_returns_none(tmp_path):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    assert get_bill_by_id(USER_ID, 999, db_path=db_path) is None


def test_update_bill(tmp_path):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    bill = add_bill(
        user_id=USER_ID,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        db_path=db_path,
    )

    updated_bill = update_bill(
        user_id=USER_ID,
        bill_id=bill.id,
        name="Electric Utility",
        amount=Decimal("140.00"),
        due_day=16,
        db_path=db_path,
    )

    assert updated_bill is not None
    assert updated_bill.name == "Electric Utility"
    assert updated_bill.amount == Decimal("140.00")
    assert updated_bill.due_day == 16
    assert updated_bill.is_paid is False


def test_update_bill_preserves_unchanged_fields(
    tmp_path,
):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    bill = add_bill(
        user_id=USER_ID,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        db_path=db_path,
    )

    updated_bill = update_bill(
        user_id=USER_ID,
        bill_id=bill.id,
        amount=Decimal("130.00"),
        db_path=db_path,
    )

    assert updated_bill is not None
    assert updated_bill.name == "Electric"
    assert updated_bill.amount == Decimal("130.00")
    assert updated_bill.due_day == 15
    assert updated_bill.is_paid is False


def test_update_bill_returns_none_when_missing(
    tmp_path,
):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    assert (
        update_bill(
            user_id=USER_ID,
            bill_id=999,
            name="Missing",
            db_path=db_path,
        )
        is None
    )


def test_mark_bill_paid(tmp_path):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    bill = add_bill(
        user_id=USER_ID,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        db_path=db_path,
    )

    updated_bill = mark_bill_paid(
        USER_ID,
        bill.id,
        db_path=db_path,
    )

    assert updated_bill is not None
    assert updated_bill.is_paid is True


def test_mark_bill_unpaid(tmp_path):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    bill = add_bill(
        user_id=USER_ID,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        is_paid=True,
        db_path=db_path,
    )

    updated_bill = mark_bill_unpaid(
        USER_ID,
        bill.id,
        db_path=db_path,
    )

    assert updated_bill is not None
    assert updated_bill.is_paid is False


def test_delete_bill(tmp_path):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    bill = add_bill(
        user_id=USER_ID,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        db_path=db_path,
    )

    deleted_bill = delete_bill(
        USER_ID,
        bill.id,
        db_path=db_path,
    )

    assert deleted_bill == bill
    assert get_bills(USER_ID, db_path=db_path) == []


def test_delete_bill_returns_none_when_missing(
    tmp_path,
):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    assert (
        delete_bill(
            USER_ID,
            999,
            db_path=db_path,
        )
        is None
    )


def test_load_bills_restores_saved_bills(
    tmp_path,
):
    db_path = tmp_path / "bills.db"
    _create_user(db_path)

    add_bill(
        user_id=USER_ID,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        db_path=db_path,
    )

    bills.clear()

    load_bills(USER_ID, db_path)

    loaded_bills = get_bills(USER_ID, db_path=db_path)

    assert len(loaded_bills) == 1
    assert loaded_bills[0].name == "Electric"
    assert loaded_bills[0].amount == 125


def test_bills_are_isolated_per_user(tmp_path):
    db_path = tmp_path / "bills.db"
    _create_user(db_path, "alice")
    _create_user(db_path, "bob")

    add_bill(
        user_id=1,
        name="Electric",
        amount=Decimal("125.00"),
        due_day=15,
        db_path=db_path,
    )
    add_bill(
        user_id=2,
        name="Internet",
        amount=Decimal("80.00"),
        due_day=20,
        db_path=db_path,
    )

    user_one_bills = get_bills(1, db_path=db_path)
    user_two_bills = get_bills(2, db_path=db_path)

    assert len(user_one_bills) == 1
    assert user_one_bills[0].name == "Electric"
    assert len(user_two_bills) == 1
    assert user_two_bills[0].name == "Internet"
