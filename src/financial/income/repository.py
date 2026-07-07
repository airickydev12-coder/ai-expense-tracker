import json

from src.core.config import DATA_DIR
from src.financial.income.models import Income


INCOME_FILE = DATA_DIR / "income.json"


def load_income_from_file() -> list[Income]:
    """Load income entries from the JSON data file."""
    if not INCOME_FILE.exists():
        return []

    with open(INCOME_FILE, "r") as file:
        raw_data = json.load(file)

    return [Income.from_dict(item) for item in raw_data]


def save_income_to_file(income_entries: list[Income]) -> None:
    """Save income entries to the JSON data file."""
    INCOME_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = [income.to_dict() for income in income_entries]

    with open(INCOME_FILE, "w") as file:
        json.dump(data, file, indent=4)