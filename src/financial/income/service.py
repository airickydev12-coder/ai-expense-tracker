from src.financial.events.bus import event_bus
from src.financial.events.event_types import FinancialEvent
from src.financial.income.models import Income
from src.financial.income.repository import (
    load_income_from_file,
    save_income_to_file,
)

income_entries: list[Income] = []


def load_income() -> None:
    """Load income entries from the repository."""
    global income_entries
    income_entries = load_income_from_file()


def save_income() -> None:
    """Save income entries using the repository."""
    save_income_to_file(income_entries)


def get_income_entries() -> list[Income]:
    """Return all income entries."""
    return income_entries.copy()


def get_next_income_id() -> int:
    """Return the next available income ID."""
    if not income_entries:
        return 1

    return max(income.id for income in income_entries) + 1


def add_income(source: str, amount: float) -> Income:
    """Create and add a new income entry."""
    income = Income(
        id=get_next_income_id(),
        source=source,
        amount=amount,
    )

    income_entries.append(income)
    save_income()
    event_bus.publish(FinancialEvent.INCOME_ADDED, income)

    return income


def delete_income(income_id: int) -> Income | None:
    """Delete an income entry by ID."""
    for index, income in enumerate(income_entries):
        if income.id == income_id:
            deleted_income = income_entries.pop(index)
            save_income()
            return deleted_income

    return None