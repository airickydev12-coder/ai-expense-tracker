from decimal import Decimal

from src.financial.debt.models import Debt


def get_total_debt(
    debts: list[Debt],
) -> Decimal:
    """Return the combined outstanding debt balance."""
    return sum(
        (debt.balance for debt in debts),
        start=Decimal("0"),
    )


def get_total_minimum_payments(
    debts: list[Debt],
) -> Decimal:
    """Return the combined minimum monthly payments."""
    return sum(
        (debt.minimum_payment for debt in debts if debt.balance > 0),
        start=Decimal("0"),
    )


def get_highest_interest_debt(
    debts: list[Debt],
) -> Debt | None:
    """Return the active debt with the highest interest rate."""
    active_debts = [debt for debt in debts if debt.balance > 0]

    if not active_debts:
        return None

    return max(
        active_debts,
        key=lambda debt: debt.interest_rate,
    )


def get_debt_count(
    debts: list[Debt],
) -> int:
    """Return the number of active debts."""
    return sum(1 for debt in debts if debt.balance > 0)


def is_debt_paid_off(
    debt: Debt,
) -> bool:
    """Return whether a debt has been paid off."""
    return debt.balance <= 0
