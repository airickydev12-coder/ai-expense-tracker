from dataclasses import dataclass


@dataclass
class Bill:
    """Represents a recurring bill."""

    id: int
    name: str
    amount: float
    due_day: int
    is_paid: bool = False

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValueError("Bill ID must be greater than zero.")

        if not self.name.strip():
            raise ValueError("Bill name cannot be empty.")

        if self.amount < 0:
            raise ValueError("Bill amount cannot be negative.")

        if self.due_day < 1 or self.due_day > 31:
            raise ValueError("Due day must be between 1 and 31.")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "due_day": self.due_day,
            "is_paid": self.is_paid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bill":
        return cls(
            id=int(data["id"]),
            name=data["name"],
            amount=float(data["amount"]),
            due_day=int(data["due_day"]),
            is_paid=bool(data["is_paid"]),
        )