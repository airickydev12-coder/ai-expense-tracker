from dataclasses import dataclass

from src.financial.categories import ExpenseCategory


@dataclass
class Budget:
    """Represents a spending budget for a category."""

    category: ExpenseCategory
    limit: float

    def __post_init__(self) -> None:
        if self.limit < 0:
            raise ValueError("Budget limit cannot be negative.")