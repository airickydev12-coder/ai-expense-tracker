from decimal import Decimal
from pathlib import Path

from src.core.config import DB_PATH
from src.core.exceptions import ValidationError
from src.core.logging import get_logger
from src.financial.debt.models import Debt
from src.financial.debt.repository import (
    load_debts_from_file,
    save_debts_to_file,
)

logger = get_logger(__name__)

ZERO_MONEY = Decimal("0")

debts: dict[int, list[Debt]] = {}


def _ensure_loaded(user_id: int, db_path: Path = DB_PATH) -> None:
    """Lazily load a user's debts into the cache on first access."""
    if user_id not in debts:
        debts[user_id] = load_debts_from_file(user_id, db_path)


def load_debts(user_id: int, db_path: Path = DB_PATH) -> None:
    """Force-reload a user's debts from the repository."""
    debts[user_id] = load_debts_from_file(user_id, db_path)


def save_debts(user_id: int, db_path: Path = DB_PATH) -> None:
    """Save a user's debts using the repository."""
    save_debts_to_file(debts[user_id], user_id, db_path)


def get_debts(user_id: int, db_path: Path = DB_PATH) -> list[Debt]:
    """Return a copy of all of this user's debts."""
    _ensure_loaded(user_id, db_path)
    return debts[user_id].copy()


def get_debt_by_id(
    user_id: int,
    debt_id: int,
    db_path: Path = DB_PATH,
) -> Debt | None:
    """Return one of this user's debts by ID."""
    _ensure_loaded(user_id, db_path)

    for debt in debts[user_id]:
        if debt.id == debt_id:
            return debt

    return None


def get_next_debt_id(user_id: int, db_path: Path = DB_PATH) -> int:
    """Return the next available debt ID for this user."""
    _ensure_loaded(user_id, db_path)
    user_debts = debts[user_id]
    if not user_debts:
        return 1

    return max(debt.id for debt in user_debts) + 1


def add_debt(
    user_id: int,
    name: str,
    balance: Decimal,
    interest_rate: float,
    minimum_payment: Decimal,
    db_path: Path = DB_PATH,
) -> Debt:
    """Create and save a debt for this user."""
    _ensure_loaded(user_id, db_path)

    debt = Debt(
        id=get_next_debt_id(user_id, db_path),
        name=name,
        balance=balance,
        interest_rate=interest_rate,
        minimum_payment=minimum_payment,
    )

    debts[user_id].append(debt)
    save_debts(user_id, db_path)

    logger.info(
        "Added debt %d (%s) for user %d",
        debt.id,
        debt.name,
        user_id,
    )

    return debt


def update_debt(
    user_id: int,
    debt_id: int,
    name: str | None = None,
    balance: Decimal | None = None,
    interest_rate: float | None = None,
    minimum_payment: Decimal | None = None,
    db_path: Path = DB_PATH,
) -> Debt | None:
    """Update one of this user's existing debts."""
    _ensure_loaded(user_id, db_path)

    debt = get_debt_by_id(user_id, debt_id, db_path)

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

    debt_index = debts[user_id].index(debt)
    debts[user_id][debt_index] = updated_debt

    save_debts(user_id, db_path)

    logger.info(
        "Updated debt %d for user %d",
        debt_id,
        user_id,
    )

    return updated_debt


def apply_payment_to_debt(
    user_id: int,
    debt_id: int,
    payment: Decimal,
    db_path: Path = DB_PATH,
) -> Debt | None:
    """Apply a payment to one of this user's existing debts."""
    if payment < ZERO_MONEY:
        raise ValidationError("Debt payment cannot be negative.")

    _ensure_loaded(user_id, db_path)

    debt = get_debt_by_id(user_id, debt_id, db_path)

    if debt is None:
        return None

    updated_balance = max(
        debt.balance - payment,
        ZERO_MONEY,
    )

    updated_debt = update_debt(
        user_id=user_id,
        debt_id=debt.id,
        balance=updated_balance,
        db_path=db_path,
    )

    logger.info(
        "Applied payment of %s to debt %d for user %d",
        payment,
        debt_id,
        user_id,
    )

    return updated_debt


def delete_debt(
    user_id: int,
    debt_id: int,
    db_path: Path = DB_PATH,
) -> Debt | None:
    """Delete one of this user's debts by ID."""
    _ensure_loaded(user_id, db_path)

    for index, debt in enumerate(debts[user_id]):
        if debt.id == debt_id:
            deleted_debt = debts[user_id].pop(index)
            save_debts(user_id, db_path)
            logger.info(
                "Deleted debt %d for user %d",
                debt_id,
                user_id,
            )
            return deleted_debt

    return None
