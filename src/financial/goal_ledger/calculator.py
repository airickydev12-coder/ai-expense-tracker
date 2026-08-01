from collections.abc import Iterable
from decimal import Decimal

from src.core.exceptions import ValidationError
from src.core.money import (
    ZERO,
    add_money,
)
from src.financial.goal_ledger.models import (
    GoalLedgerEntry,
    GoalLedgerEntryType,
)


def get_signed_entry_amount(
    entry: GoalLedgerEntry,
) -> Decimal:
    """
    Return the signed balance effect
    of a ledger entry.
    """

    if entry.entry_type in {
        GoalLedgerEntryType.OPENING_BALANCE,
        GoalLedgerEntryType.CONTRIBUTION,
    }:
        return entry.amount

    if entry.entry_type in {
        GoalLedgerEntryType.WITHDRAWAL,
        GoalLedgerEntryType.REVERSAL,
    }:
        return -entry.amount

    return entry.amount


def calculate_goal_balance(
    entries: Iterable[GoalLedgerEntry],
    *,
    goal_id: int,
) -> Decimal:
    """
    Calculate one goal balance.
    """

    if goal_id <= 0:
        raise ValidationError("Goal ID must be greater than zero.")

    balance = ZERO

    for entry in entries:

        if entry.goal_id != goal_id:
            continue

        balance = add_money(
            balance,
            get_signed_entry_amount(entry),
        )

    return balance


def calculate_all_goal_balances(
    entries: Iterable[GoalLedgerEntry],
) -> dict[int, Decimal]:
    """
    Calculate balances for all goals.
    """

    balances: dict[int, Decimal] = {}

    for entry in entries:

        current = balances.get(
            entry.goal_id,
            ZERO,
        )

        balances[entry.goal_id] = add_money(
            current,
            get_signed_entry_amount(entry),
        )

    return balances
