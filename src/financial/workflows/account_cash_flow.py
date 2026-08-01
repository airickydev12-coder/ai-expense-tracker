from src.financial.accounts.models import Account
from decimal import Decimal


def apply_cash_flow_to_account(
    account: Account,
    net_cash_flow: Decimal,
) -> Account:
    """Apply net cash flow to an account balance."""
    account.balance += net_cash_flow
    return account
