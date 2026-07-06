from dataclasses import dataclass

from src.financial.categories import ExpenseCategory


@dataclass
class Expense:
    """Represents a single financial expense."""

    id: int
    name: str
    category: ExpenseCategory
    amount: float

    def __post_init__(self) -> None:
        """Validate the expense after initialization."""
        if self.id <= 0:
            raise ValueError("Expense ID must be greater than zero.")

        if not self.name.strip():
            raise ValueError("Expense name cannot be empty.")

        if self.amount < 0:
            raise ValueError("Expense amount cannot be negative.")

        if not isinstance(self.category, ExpenseCategory):
            self.category = ExpenseCategory(self.category)

    def to_dict(self) -> dict:
        """Convert the expense to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "amount": self.amount,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        """Create an Expense from a dictionary."""
        return cls(
            id=int(data["id"]),
            name=data["name"],
            category=ExpenseCategory(data["category"]),
            amount=float(data["amount"]),
        )