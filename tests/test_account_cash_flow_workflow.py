from src.financial.accounts.models import Account
from src.financial.workflows.account_cash_flow import apply_cash_flow_to_account


def test_apply_positive_cash_flow_to_account():
    account = Account(
        id=1,
        name="Checking",
        account_type="Bank",
        balance=1000,
    )

    updated_account = apply_cash_flow_to_account(account, 500)

    assert updated_account.balance == 1500


def test_apply_negative_cash_flow_to_account():
    account = Account(
        id=1,
        name="Checking",
        account_type="Bank",
        balance=1000,
    )

    updated_account = apply_cash_flow_to_account(account, -300)

    assert updated_account.balance == 700