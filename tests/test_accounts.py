import pytest

from src.financial.accounts.models import Account

from decimal import Decimal


def test_account_creation():
    account = Account(
        id=1,
        name="Checking",
        account_type="Bank",
        balance=Decimal("1500"),
    )

    assert account.id == 1
    assert account.name == "Checking"
    assert account.account_type == "Bank"
    assert account.balance == Decimal("1500")


def test_account_invalid_id():
    with pytest.raises(ValueError):
        Account(id=0, name="Checking", account_type="Bank", balance=Decimal("1500"))


def test_account_empty_name():
    with pytest.raises(ValueError):
        Account(id=1, name="", account_type="Bank", balance=Decimal("1500"))


def test_account_empty_type():
    with pytest.raises(ValueError):
        Account(id=1, name="Checking", account_type="", balance=Decimal("1500"))
