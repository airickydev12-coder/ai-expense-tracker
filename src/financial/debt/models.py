from dataclasses import dataclass


@dataclass
class Debt:
    """Represents a financial debt account."""

    id: int
    name: str
    balance: float
    interest_rate: float
    minimum_payment: float

    def __post_init__(self) -> None:
        """Validate the debt after initialization."""
        if self.id <= 0:
            raise ValueError("Debt ID must be greater than zero.")

        if not self.name.strip():
            raise ValueError("Debt name cannot be empty.")

        if self.balance < 0:
            raise ValueError("Debt balance cannot be negative.")

        if self.interest_rate < 0:
            raise ValueError("Debt interest rate cannot be negative.")

        if self.minimum_payment < 0:
            raise ValueError("Debt minimum payment cannot be negative.")

    def to_dict(self) -> dict:
        """Convert the debt to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "name": self.name,
            "balance": self.balance,
            "interest_rate": self.interest_rate,
            "minimum_payment": self.minimum_payment,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Debt":
        """Create a Debt from a dictionary."""
        return cls(
            id=int(data["id"]),
            name=data["name"],
            balance=float(data["balance"]),
            interest_rate=float(data["interest_rate"]),
            minimum_payment=float(data["minimum_payment"]),
        )