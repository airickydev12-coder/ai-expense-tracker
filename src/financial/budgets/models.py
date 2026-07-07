from dataclasses import dataclass

from src.financial.categories import ExpenseCategory


@dataclass
class Budget:
    """Represents a spending budget for a category."""

    category: ExpenseCategory
    limit: float

    def __post_init__(self) -> None:
        """Validate the budget after initialization."""
        if self.limit < 0:
            raise ValueError("Budget limit cannot be negative.")

        if not isinstance(self.category, ExpenseCategory):
            self.category = ExpenseCategory(self.category)

    def to_dict(self) -> dict:
        """Convert the budget to a dictionary for JSON storage."""
        return {
            "category": self.category.value,
            "limit": self.limit,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Budget":
        """Create a Budget from a dictionary."""
        return cls(
            category=ExpenseCategory(data["category"]),
            limit=float(data["limit"]),
        )