from dataclasses import dataclass
from decimal import Decimal

from src.core.money import (
    money_from_json,
    money_to_json,
    to_money,
)


@dataclass
class Debt:
    """Represents a financial debt account."""

    id: int
    name: str
    balance: Decimal
    interest_rate: float
    minimum_payment: Decimal

    def __post_init__(self) -> None:
        """Validate and normalize the debt after initialization."""
        self.balance = to_money(self.balance)
        self.minimum_payment = to_money(self.minimum_payment)

        if not isinstance(self.interest_rate, float):
            self.interest_rate = float(self.interest_rate)

        if self.id <= 0:
            raise ValueError("Debt ID must be greater than zero.")

        if not self.name.strip():
            raise ValueError("Debt name cannot be empty.")

        if self.balance < Decimal("0.00"):
            raise ValueError("Debt balance cannot be negative.")

        if self.interest_rate < 0:
            raise ValueError("Debt interest rate cannot be negative.")

        if self.minimum_payment < Decimal("0.00"):
            raise ValueError("Debt minimum payment cannot be negative.")

    def to_dict(self) -> dict:
        """Convert the debt to JSON-compatible data."""
        return {
            "id": self.id,
            "name": self.name,
            "balance": money_to_json(self.balance),
            "interest_rate": self.interest_rate,
            "minimum_payment": money_to_json(self.minimum_payment),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Debt":
        """Create a Debt from JSON data."""
        return cls(
            id=int(data["id"]),
            name=data["name"],
            balance=money_from_json(str(data["balance"])),
            interest_rate=float(data["interest_rate"]),
            minimum_payment=money_from_json(str(data["minimum_payment"])),
        )
