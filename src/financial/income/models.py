from dataclasses import dataclass


@dataclass
class Income:
    """Represents a single income entry."""

    id: int
    source: str
    amount: float

    def __post_init__(self) -> None:
        """Validate the income after initialization."""
        if self.id <= 0:
            raise ValueError("Income ID must be greater than zero.")

        if not self.source.strip():
            raise ValueError("Income source cannot be empty.")

        if self.amount < 0:
            raise ValueError("Income amount cannot be negative.")

    def to_dict(self) -> dict:
        """Convert the income to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "source": self.source,
            "amount": self.amount,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Income":
        """Create an Income from a dictionary."""
        return cls(
            id=int(data["id"]),
            source=data["source"],
            amount=float(data["amount"]),
        )