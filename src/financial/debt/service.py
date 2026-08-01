from decimal import Decimal
from pathlib import Path

from src.core.exceptions import ValidationError
from src.core.logging import get_logger
from src.financial.debt.models import Debt
from src.financial.debt.repository import (
    DEBTS_FILE,
    load_debts_from_file,
    save_debts_to_file,
)

logger = get_logger(__name__)

ZERO_MONEY = Decimal("0")

debts: list[Debt] = []


def load_debts(
    file_path: Path = DEBTS_FILE,
) -> None:
    """Load debts into application memory."""
    debts.clear()
    debts.extend(load_debts_from_file(file_path))


def save_debts(
    file_path: Path = DEBTS_FILE,
) -> None:
    """Save all debts from application memory."""
    save_debts_to_file(
        debts,
        file_path,
    )


def get_debts() -> list[Debt]:
    """Return a copy of all debts."""
    return debts.copy()


def get_debt_by_id(
    debt_id: int,
) -> Debt | None:
    """Return a debt by ID."""
    for debt in debts:
        if debt.id == debt_id:
            return debt

    return None


def get_next_debt_id() -> int:
    """Return the next available debt ID."""
    if not debts:
        return 1

    return max(debt.id for debt in debts) + 1


def add_debt(
    name: str,
    balance: Decimal,
    interest_rate: float,
    minimum_payment: Decimal,
    file_path: Path = DEBTS_FILE,
) -> Debt:
    """Create and save a debt."""
    debt = Debt(
        id=get_next_debt_id(),
        name=name,
        balance=balance,
        interest_rate=interest_rate,
        minimum_payment=minimum_payment,
    )

    debts.append(debt)
    save_debts(file_path)

    logger.info(
        "Added debt %d (%s)",
        debt.id,
        debt.name,
    )

    return debt


def update_debt(
    debt_id: int,
    name: str | None = None,
    balance: Decimal | None = None,
    interest_rate: float | None = None,
    minimum_payment: Decimal | None = None,
    file_path: Path = DEBTS_FILE,
) -> Debt | None:
    """Update an existing debt."""
    debt = get_debt_by_id(debt_id)

    if debt is None:
        return None

    updated_debt = Debt(
        id=debt.id,
        name=(name.strip() if name is not None else debt.name),
        balance=(balance if balance is not None else debt.balance),
        interest_rate=(
            interest_rate if interest_rate is not None else debt.interest_rate
        ),
        minimum_payment=(
            minimum_payment if minimum_payment is not None else debt.minimum_payment
        ),
    )

    debt_index = debts.index(debt)
    debts[debt_index] = updated_debt

    save_debts(file_path)

    logger.info(
        "Updated debt %d",
        debt_id,
    )

    return updated_debt


def apply_payment_to_debt(
    debt_id: int,
    payment: Decimal,
    file_path: Path = DEBTS_FILE,
) -> Debt | None:
    """Apply a payment to an existing debt."""
    if payment < ZERO_MONEY:
        raise ValidationError("Debt payment cannot be negative.")

    debt = get_debt_by_id(debt_id)

    if debt is None:
        return None

    updated_balance = max(
        debt.balance - payment,
        ZERO_MONEY,
    )

    updated_debt = update_debt(
        debt_id=debt.id,
        balance=updated_balance,
        file_path=file_path,
    )

    logger.info(
        "Applied payment of %s to debt %d",
        payment,
        debt_id,
    )

    return updated_debt


def delete_debt(
    debt_id: int,
    file_path: Path = DEBTS_FILE,
) -> Debt | None:
    """Delete a debt by ID."""
    for index, debt in enumerate(debts):
        if debt.id == debt_id:
            deleted_debt = debts.pop(index)
            save_debts(file_path)
            logger.info(
                "Deleted debt %d",
                debt_id,
            )
            return deleted_debt

    return None
