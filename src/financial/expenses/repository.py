import json

from src.core.config import DATA_FILE
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.expenses.models import Expense

logger = get_logger(__name__)


def load_expenses_from_file() -> list[Expense]:
    """
    Load expenses from the JSON data file.

    Returns:
        list[Expense]: Expenses loaded from storage.
    """
    if not DATA_FILE.exists():
        return []

    try:
        with open(DATA_FILE, "r") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError as error:
        logger.error(
            "Failed to parse expenses file %s: %s",
            DATA_FILE,
            error,
        )
        raise PersistenceError(
            f"Expense data file contains invalid JSON: {DATA_FILE}"
        ) from error

    if not isinstance(raw_data, list):
        raise PersistenceError("Expense data must be stored as a JSON list.")

    expenses = [Expense.from_dict(item) for item in raw_data]

    logger.debug(
        "Loaded %d expense(s) from %s",
        len(expenses),
        DATA_FILE,
    )

    return expenses


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

    logger.debug(
        "Saved %d expense(s) to %s",
        len(expenses),
        DATA_FILE,
    )
