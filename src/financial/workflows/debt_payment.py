from decimal import Decimal

from src.core.exceptions import ValidationError
from src.financial.debt.models import Debt


def apply_debt_payment(
    debt: Debt,
    payment: Decimal,
) -> Debt:
    """
    Apply a payment toward a debt.

    Args:
        debt: Debt being paid.
        payment: Payment amount.

    Returns:
        Updated debt.
    """
    if payment < Decimal("0"):
        raise ValidationError("Payment cannot be negative.")

    debt.balance -= payment

    if debt.balance < Decimal("0"):
        debt.balance = Decimal("0")

    return debt
