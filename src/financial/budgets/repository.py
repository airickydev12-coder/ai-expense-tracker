import json

from src.core.config import DATA_DIR
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.budgets.models import Budget

logger = get_logger(__name__)

BUDGET_FILE = DATA_DIR / "budgets.json"


def load_budgets_from_file() -> list[Budget]:
    """Load budgets from the JSON data file."""
    if not BUDGET_FILE.exists():
        return []

    try:
        with open(BUDGET_FILE, "r") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError as error:
        logger.error(
            "Failed to parse budgets file %s: %s",
            BUDGET_FILE,
            error,
        )
        raise PersistenceError(
            f"Budget data file contains invalid JSON: {BUDGET_FILE}"
        ) from error

    if not isinstance(raw_data, list):
        raise PersistenceError("Budget data must be stored as a JSON list.")

    budgets = [Budget.from_dict(item) for item in raw_data]

    logger.debug(
        "Loaded %d budget(s) from %s",
        len(budgets),
        BUDGET_FILE,
    )

    return budgets


def save_budgets_to_file(budgets: list[Budget]) -> None:
    """Save budgets to the JSON data file."""
    BUDGET_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = [budget.to_dict() for budget in budgets]

    with open(BUDGET_FILE, "w") as file:
        json.dump(data, file, indent=4)

    logger.debug(
        "Saved %d budget(s) to %s",
        len(budgets),
        BUDGET_FILE,
    )
