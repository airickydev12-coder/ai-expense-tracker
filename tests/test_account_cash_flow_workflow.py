from decimal import Decimal

from src.financial.accounts.models import Account
from src.financial.workflows.account_cash_flow import apply_cash_flow_to_account


def test_apply_positive_cash_flow_to_account():
    account = Account(
        id=1,
        name="Checking",
        account_type="Bank",
        balance=Decimal("1000"),
    )

    updated_account = apply_cash_flow_to_account(
        account,
        Decimal("500"),
    )

    assert updated_account.balance == Decimal("1500")


def test_apply_negative_cash_flow_to_account():
    account = Account(
        id=1,
        name="Checking",
        account_type="Bank",
        balance=Decimal("1000"),
    )

    updated_account = apply_cash_flow_to_account(
        account,
        Decimal("-300"),
    )

    assert updated_account.balance == Decimal("700")
