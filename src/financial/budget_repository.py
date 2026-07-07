import json

from src.core.config import DATA_DIR
from src.financial.budget_models import Budget


BUDGET_FILE = DATA_DIR / "budgets.json"


def load_budgets_from_file() -> list[Budget]:
    """Load budgets from the JSON data file."""
    if not BUDGET_FILE.exists():
        return []

    with open(BUDGET_FILE, "r") as file:
        raw_data = json.load(file)

    return [Budget.from_dict(item) for item in raw_data]


def save_budgets_to_file(budgets: list[Budget]) -> None:
    """Save budgets to the JSON data file."""
    BUDGET_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = [budget.to_dict() for budget in budgets]

    with open(BUDGET_FILE, "w") as file:
        json.dump(data, file, indent=4)