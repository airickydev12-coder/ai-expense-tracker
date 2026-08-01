import json

from src.core.config import DATA_DIR
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.income.models import Income

logger = get_logger(__name__)

INCOME_FILE = DATA_DIR / "income.json"


def load_income_from_file() -> list[Income]:
    """Load income entries from the JSON data file."""
    if not INCOME_FILE.exists():
        return []

    try:
        with open(INCOME_FILE, "r") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError as error:
        logger.error(
            "Failed to parse income file %s: %s",
            INCOME_FILE,
            error,
        )
        raise PersistenceError(
            f"Income data file contains invalid JSON: {INCOME_FILE}"
        ) from error

    if not isinstance(raw_data, list):
        raise PersistenceError("Income data must be stored as a JSON list.")

    income_entries = [Income.from_dict(item) for item in raw_data]

    logger.debug(
        "Loaded %d income entry(ies) from %s",
        len(income_entries),
        INCOME_FILE,
    )

    return income_entries


def save_income_to_file(income_entries: list[Income]) -> None:
    """Save income entries to the JSON data file."""
    INCOME_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = [income.to_dict() for income in income_entries]

    with open(INCOME_FILE, "w") as file:
        json.dump(data, file, indent=4)

    logger.debug(
        "Saved %d income entry(ies) to %s",
        len(income_entries),
        INCOME_FILE,
    )