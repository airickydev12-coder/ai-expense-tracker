from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from src.core.exceptions import ValidationError
from src.financial.shared.categories import ExpenseCategory


class RecurrenceFrequency(Enum):
    """How often a recurring expense template recurs."""

    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


@dataclass
class RecurringExpenseTemplate:
    """Represents a recurring expense that periodically spawns real expenses."""

    id: int
    name: str
    category: ExpenseCategory
    amount: Decimal
    frequency: RecurrenceFrequency
    next_occurrence: date
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate the template after initialization."""
        if self.id <= 0:
            raise ValidationError("Recurring expense template ID must be greater than zero.")

        if not self.name.strip():
            raise ValidationError("Recurring expense template name cannot be empty.")

        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))

        if self.amount < Decimal("0"):
            raise ValidationError("Recurring expense template amount cannot be negative.")

        if not isinstance(self.category, ExpenseCategory):
            self.category = ExpenseCategory(self.category)

        if not isinstance(self.frequency, RecurrenceFrequency):
            self.frequency = RecurrenceFrequency(self.frequency)

    def to_dict(self) -> dict:
        """Convert the template to a dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "amount": str(self.amount),
            "frequency": self.frequency.value,
            "next_occurrence": self.next_occurrence.isoformat(),
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecurringExpenseTemplate":
        """Create a RecurringExpenseTemplate from a dictionary."""
        return cls(
            id=int(data["id"]),
            name=data["name"],
            category=ExpenseCategory(data["category"]),
            amount=Decimal(str(data["amount"])),
            frequency=RecurrenceFrequency(data["frequency"]),
            next_occurrence=date.fromisoformat(str(data["next_occurrence"])),
            is_active=bool(data["is_active"]),
        )
