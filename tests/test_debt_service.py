from decimal import Decimal

import pytest

from src.financial.debt.service import (
    add_debt,
    apply_payment_to_debt,
    debts,
    delete_debt,
    get_debt_by_id,
    get_debts,
    get_next_debt_id,
    load_debts,
    update_debt,
)
from src.financial.users.repository import create_user

USER_ID = 1


def setup_function():
    """Clear debt state before every test."""
    debts.clear()


def _create_user(file_path) -> None:
    """Insert a throwaway user row so debts' FK constraint is satisfied."""
    create_user("alice", "alice@example.com", "hash", file_path)


def test_add_debt(tmp_path):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    debt = add_debt(
        user_id=USER_ID,
        name="Credit Card",
        balance=Decimal("2500"),
        interest_rate=24.99,
        minimum_payment=Decimal("75"),
        db_path=file_path,
    )

    assert debt.id == 1
    assert debt.name == "Credit Card"
    assert debt.balance == Decimal("2500")
    assert debt.interest_rate == 24.99
    assert debt.minimum_payment == Decimal("75")
    assert file_path.exists()


def test_add_multiple_debts_assigns_unique_ids(
    tmp_path,
):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    first_debt = add_debt(
        user_id=USER_ID,
        name="Credit Card",
        balance=Decimal("2500"),
        interest_rate=24.99,
        minimum_payment=Decimal("75"),
        db_path=file_path,
    )

    second_debt = add_debt(
        user_id=USER_ID,
        name="Car Loan",
        balance=Decimal("12000"),
        interest_rate=6.5,
        minimum_payment=Decimal("350"),
        db_path=file_path,
    )

    assert first_debt.id == 1
    assert second_debt.id == 2
    assert get_next_debt_id(USER_ID) == 3


def test_get_debts_returns_copy(
    tmp_path,
):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    add_debt(
        user_id=USER_ID,
        name="Credit Card",
        balance=Decimal("2500"),
        interest_rate=24.99,
        minimum_payment=Decimal("75"),
        db_path=file_path,
    )

    returned_debts = get_debts(USER_ID, db_path=file_path)
    returned_debts.clear()

    assert len(debts[USER_ID]) == 1


def test_get_debt_by_id(tmp_path):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    created_debt = add_debt(
        user_id=USER_ID,
        name="Credit Card",
        balance=Decimal("2500"),
        interest_rate=24.99,
        minimum_payment=Decimal("75"),
        db_path=file_path,
    )

    assert get_debt_by_id(USER_ID, created_debt.id, db_path=file_path) == created_debt


def test_get_debt_by_id_returns_none(tmp_path):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    assert get_debt_by_id(USER_ID, 999, db_path=file_path) is None


def test_update_debt(tmp_path):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    debt = add_debt(
        user_id=USER_ID,
        name="Credit Card",
        balance=Decimal("2500"),
        interest_rate=24.99,
        minimum_payment=Decimal("75"),
        db_path=file_path,
    )

    updated_debt = update_debt(
        user_id=USER_ID,
        debt_id=debt.id,
        name="Primary Credit Card",
        balance=Decimal("2000"),
        minimum_payment=Decimal("100"),
        db_path=file_path,
    )

    assert updated_debt is not None
    assert updated_debt.name == "Primary Credit Card"
    assert updated_debt.balance == Decimal("2000")
    assert updated_debt.interest_rate == 24.99
    assert updated_debt.minimum_payment == Decimal("100")


def test_update_debt_preserves_unchanged_fields(
    tmp_path,
):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    debt = add_debt(
        user_id=USER_ID,
        name="Credit Card",
        balance=Decimal("2500"),
        interest_rate=24.99,
        minimum_payment=Decimal("75"),
        db_path=file_path,
    )

    updated_debt = update_debt(
        user_id=USER_ID,
        debt_id=debt.id,
        balance=Decimal("2200"),
        db_path=file_path,
    )

    assert updated_debt is not None
    assert updated_debt.name == "Credit Card"
    assert updated_debt.balance == Decimal("2200")
    assert updated_debt.interest_rate == 24.99
    assert updated_debt.minimum_payment == Decimal("75")


def test_update_debt_returns_none_when_missing(
    tmp_path,
):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    assert (
        update_debt(
            user_id=USER_ID,
            debt_id=999,
            name="Missing",
            db_path=file_path,
        )
        is None
    )


def test_apply_payment_to_debt(tmp_path):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    debt = add_debt(
        user_id=USER_ID,
        name="Credit Card",
        balance=Decimal("2500"),
        interest_rate=24.99,
        minimum_payment=Decimal("75"),
        db_path=file_path,
    )

    updated_debt = apply_payment_to_debt(
        user_id=USER_ID,
        debt_id=debt.id,
        payment=Decimal("500"),
        db_path=file_path,
    )

    assert updated_debt is not None
    assert updated_debt.balance == Decimal("2000")


def test_overpayment_sets_balance_to_zero(
    tmp_path,
):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    debt = add_debt(
        user_id=USER_ID,
        name="Credit Card",
        balance=Decimal("500"),
        interest_rate=24.99,
        minimum_payment=Decimal("75"),
        db_path=file_path,
    )

    updated_debt = apply_payment_to_debt(
        user_id=USER_ID,
        debt_id=debt.id,
        payment=Decimal("1000"),
        db_path=file_path,
    )

    assert updated_debt is not None
    assert updated_debt.balance == Decimal("0")


def test_negative_debt_payment_raises_error(
    tmp_path,
):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    debt = add_debt(
        user_id=USER_ID,
        name="Credit Card",
        balance=Decimal("500"),
        interest_rate=24.99,
        minimum_payment=Decimal("75"),
        db_path=file_path,
    )

    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        apply_payment_to_debt(
            user_id=USER_ID,
            debt_id=debt.id,
            payment=Decimal("-100"),
            db_path=file_path,
        )


def test_delete_debt(tmp_path):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    debt = add_debt(
        user_id=USER_ID,
        name="Credit Card",
        balance=Decimal("2500"),
        interest_rate=24.99,
        minimum_payment=Decimal("75"),
        db_path=file_path,
    )

    deleted_debt = delete_debt(
        USER_ID,
        debt.id,
        db_path=file_path,
    )

    assert deleted_debt == debt
    assert get_debts(USER_ID, db_path=file_path) == []


def test_delete_debt_returns_none_when_missing(
    tmp_path,
):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    assert (
        delete_debt(
            USER_ID,
            999,
            db_path=file_path,
        )
        is None
    )


def test_load_debts_restores_saved_debts(
    tmp_path,
):
    file_path = tmp_path / "debts.db"
    _create_user(file_path)

    add_debt(
        user_id=USER_ID,
        name="Credit Card",
        balance=Decimal("2500"),
        interest_rate=24.99,
        minimum_payment=Decimal("75"),
        db_path=file_path,
    )

    debts.clear()

    load_debts(USER_ID, file_path)

    loaded_debts = get_debts(USER_ID, db_path=file_path)

    assert len(loaded_debts) == 1
    assert loaded_debts[0].name == "Credit Card"
    assert loaded_debts[0].balance == Decimal("2500")
