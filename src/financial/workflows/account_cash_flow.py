from src.financial.accounts.models import Account


def apply_cash_flow_to_account(
    account: Account,
    net_cash_flow: float,
) -> Account:
    """Apply net cash flow to an account balance."""
    account.balance += net_cash_flow
    return account