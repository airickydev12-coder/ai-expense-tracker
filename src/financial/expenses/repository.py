import json

from src.core.config import DATA_FILE
from src.financial.expenses.models import Expense


def load_expenses_from_file() -> list[Expense]:
    """
    Load expenses from the JSON data file.

    Returns:
        list[Expense]: Expenses loaded from storage.
    """
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r") as file:
        raw_data = json.load(file)

    return [Expense.from_dict(item) for item in raw_data]


def save_expenses_to_file(expenses: list[Expense]) -> None:
    """
    Save expenses to the JSON data file.

    Args:
        expenses: Expenses to save.

    Returns:
        None
    """
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = [expense.to_dict() for expense in expenses]

    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)
