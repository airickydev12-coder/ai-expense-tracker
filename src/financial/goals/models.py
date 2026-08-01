from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.core.exceptions import ValidationError
from src.core.money import (
    money_from_json,
    money_to_json,
    to_money,
)


@dataclass
class Goal:
    """Represents a financial goal."""

    id: int
    name: str
    target_amount: Decimal
    current_amount: Decimal

    def __post_init__(self) -> None:
        """Validate and normalize the goal."""
        self.target_amount = to_money(self.target_amount)
        self.current_amount = to_money(self.current_amount)

        if self.id <= 0:
            raise ValidationError("Goal ID must be greater than zero.")

        if not self.name.strip():
            raise ValidationError("Goal name cannot be empty.")

        if self.target_amount <= Decimal("0.00"):
            raise ValidationError("Goal target amount must be greater than zero.")

        if self.current_amount < Decimal("0.00"):
            raise ValidationError("Goal current amount cannot be negative.")

    def to_dict(self) -> dict:
        """Convert the goal into JSON-compatible data."""
        return {
            "id": self.id,
            "name": self.name,
            "target_amount": money_to_json(self.target_amount),
            "current_amount": money_to_json(self.current_amount),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> "Goal":
        """Create a Goal from JSON data."""
        return cls(
            id=int(data["id"]),
            name=data["name"],
            target_amount=money_from_json(str(data["target_amount"])),
            current_amount=money_from_json(str(data["current_amount"])),
        )
