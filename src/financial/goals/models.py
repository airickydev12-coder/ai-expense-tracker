from dataclasses import dataclass


@dataclass
class Goal:
    """Represents a financial goal."""

    id: int
    name: str
    target_amount: float
    current_amount: float

    def __post_init__(self) -> None:
        """Validate the goal after initialization."""
        if self.id <= 0:
            raise ValueError("Goal ID must be greater than zero.")

        if not self.name.strip():
            raise ValueError("Goal name cannot be empty.")

        if self.target_amount <= 0:
            raise ValueError("Goal target amount must be greater than zero.")

        if self.current_amount < 0:
            raise ValueError("Goal current amount cannot be negative.")

    def to_dict(self) -> dict:
        """Convert the goal to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "name": self.name,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Goal":
        """Create a Goal from a dictionary."""
        return cls(
            id=int(data["id"]),
            name=data["name"],
            target_amount=float(data["target_amount"]),
            current_amount=float(data["current_amount"]),
        )