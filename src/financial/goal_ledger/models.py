from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from src.core.exceptions import PersistenceError, ValidationError
from src.core.money import (
    money_from_json,
    money_to_json,
    to_money,
)


class GoalLedgerEntryType(StrEnum):
    """Supported goal-ledger transaction types."""

    OPENING_BALANCE = "OPENING_BALANCE"
    CONTRIBUTION = "CONTRIBUTION"
    WITHDRAWAL = "WITHDRAWAL"
    ADJUSTMENT = "ADJUSTMENT"
    REVERSAL = "REVERSAL"


@dataclass(frozen=True)
class GoalLedgerEntry:
    """Represents one immutable ledger entry."""

    entry_id: str
    goal_id: int
    entry_type: GoalLedgerEntryType
    amount: Decimal
    effective_date: date
    created_at: datetime

    source: str = "MANUAL"
    note: str = ""
    correlation_id: str | None = None
    reverses_entry_id: str | None = None

    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "amount",
            to_money(self.amount),
        )

        try:
            UUID(self.entry_id)
        except (TypeError, ValueError) as error:
            raise ValidationError(
                "Goal ledger entry ID must be a valid UUID."
            ) from error

        if self.goal_id <= 0:
            raise ValidationError("Goal ledger goal ID must be greater than zero.")

        if not isinstance(
            self.entry_type,
            GoalLedgerEntryType,
        ):
            raise TypeError("entry_type must be GoalLedgerEntryType.")

        if self.amount == Decimal("0.00"):
            raise ValidationError("Goal ledger entry amount cannot be zero.")

        if self.entry_type in {
            GoalLedgerEntryType.OPENING_BALANCE,
            GoalLedgerEntryType.CONTRIBUTION,
            GoalLedgerEntryType.WITHDRAWAL,
            GoalLedgerEntryType.REVERSAL,
        } and self.amount < Decimal("0.00"):
            raise ValidationError(f"{self.entry_type.value} amount cannot be negative.")

        if not isinstance(
            self.effective_date,
            date,
        ):
            raise TypeError("effective_date must be a date.")

        if not isinstance(
            self.created_at,
            datetime,
        ):
            raise TypeError("created_at must be a datetime.")

        source = self.source.strip().upper()

        if not source:
            raise ValidationError("Goal ledger source cannot be empty.")

        note = self.note.strip()

        if self.created_at.tzinfo is None:
            created = self.created_at.replace(tzinfo=timezone.utc)
        else:
            created = self.created_at.astimezone(timezone.utc)

        correlation = self.correlation_id

        if correlation is not None:
            correlation = correlation.strip()

            if not correlation:
                raise ValidationError("correlation_id cannot be blank.")

        if self.entry_type is GoalLedgerEntryType.REVERSAL:

            if self.reverses_entry_id is None:
                raise ValidationError("A reversal must identify the original entry.")

            try:
                UUID(self.reverses_entry_id)
            except (TypeError, ValueError) as error:
                raise ValidationError(
                    "reverses_entry_id must be a valid UUID."
                ) from error

        elif self.reverses_entry_id is not None:
            raise ValidationError("Only reversal entries may set reverses_entry_id.")

        object.__setattr__(
            self,
            "source",
            source,
        )

        object.__setattr__(
            self,
            "note",
            note,
        )

        object.__setattr__(
            self,
            "created_at",
            created,
        )

        object.__setattr__(
            self,
            "correlation_id",
            correlation,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "goal_id": self.goal_id,
            "entry_type": self.entry_type.value,
            "amount": money_to_json(self.amount),
            "effective_date": self.effective_date.isoformat(),
            "created_at": self.created_at.isoformat(),
            "source": self.source,
            "note": self.note,
            "correlation_id": self.correlation_id,
            "reverses_entry_id": self.reverses_entry_id,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "GoalLedgerEntry":

        if not isinstance(data, dict):
            raise TypeError("Goal ledger entry data must be a dictionary.")

        try:
            return cls(
                entry_id=str(data["entry_id"]),
                goal_id=int(data["goal_id"]),
                entry_type=GoalLedgerEntryType(data["entry_type"]),
                amount=money_from_json(str(data["amount"])),
                effective_date=date.fromisoformat(str(data["effective_date"])),
                created_at=datetime.fromisoformat(str(data["created_at"])),
                source=str(
                    data.get(
                        "source",
                        "MANUAL",
                    )
                ),
                note=str(
                    data.get(
                        "note",
                        "",
                    )
                ),
                correlation_id=(
                    str(data["correlation_id"])
                    if data.get("correlation_id") is not None
                    else None
                ),
                reverses_entry_id=(
                    str(data["reverses_entry_id"])
                    if data.get("reverses_entry_id") is not None
                    else None
                ),
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise PersistenceError(
                "Goal ledger entry contains invalid data."
            ) from error
