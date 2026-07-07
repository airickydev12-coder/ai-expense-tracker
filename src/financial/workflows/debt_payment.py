from src.financial.debt.models import Debt


def apply_debt_payment(
    debt: Debt,
    payment: float,
) -> Debt:
    """
    Apply a payment toward a debt.

    Args:
        debt: Debt being paid.
        payment: Payment amount.

    Returns:
        Updated debt.
    """
    if payment < 0:
        raise ValueError("Payment cannot be negative.")

    debt.balance -= payment

    if debt.balance < 0:
        debt.balance = 0

    return debt