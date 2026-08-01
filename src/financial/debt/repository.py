import json
from pathlib import Path

from src.core.config import DATA_DIR
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.debt.models import Debt

logger = get_logger(__name__)

DEBTS_FILE = DATA_DIR / "debts.json"


def load_debts_from_file(
    file_path: Path = DEBTS_FILE,
) -> list[Debt]:
    """Load debts from a JSON file."""
    if not file_path.exists():
        return []

    try:
        with file_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError as error:
        logger.error(
            "Failed to parse debts file %s: %s",
            file_path,
            error,
        )
        raise PersistenceError(
            f"Debt data file contains invalid JSON: {file_path}"
        ) from error

    if not isinstance(raw_data, list):
        raise PersistenceError("Debt data must be stored as a JSON list.")

    debts = [
        Debt.from_dict(debt_data)
        for debt_data in raw_data
    ]

    logger.debug(
        "Loaded %d debt(s) from %s",
        len(debts),
        file_path,
    )

    return debts


def save_debts_to_file(
    debts: list[Debt],
    file_path: Path = DEBTS_FILE,
) -> None:
    """Save debts to a JSON file."""
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    debt_data = [
        debt.to_dict()
        for debt in debts
    ]

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            debt_data,
            file,
            indent=4,
        )

    logger.debug(
        "Saved %d debt(s) to %s",
        len(debts),
        file_path,
    )