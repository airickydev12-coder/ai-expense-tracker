from dataclasses import dataclass


@dataclass
class Expense:
    """Represents a single financial expense."""

    id: int
    name: str
    category: str
    amount: float

    def to_dict(self) -> dict:
        """Convert the expense to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "amount": self.amount,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        """Create an Expense from a dictionary."""
        return cls(
            id=int(data["id"]),
            name=data["name"],
            category=data["category"],
            amount=float(data["amount"]),
        )