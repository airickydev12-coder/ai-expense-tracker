import json
from pathlib import Path

from src.core.config import DATA_DIR
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.bills.models import Bill

logger = get_logger(__name__)

BILLS_FILE = DATA_DIR / "bills.json"


def load_bills_from_file(
    file_path: Path = BILLS_FILE,
) -> list[Bill]:
    """Load bills from a JSON file."""
    if not file_path.exists():
        return []

    try:
        with file_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError as error:
        logger.error(
            "Failed to parse bills file %s: %s",
            file_path,
            error,
        )
        raise PersistenceError(
            f"Bill data file contains invalid JSON: {file_path}"
        ) from error

    if not isinstance(raw_data, list):
        raise PersistenceError("Bill data must be stored as a JSON list.")

    bills = [
        Bill.from_dict(bill_data)
        for bill_data in raw_data
    ]

    logger.debug(
        "Loaded %d bill(s) from %s",
        len(bills),
        file_path,
    )

    return bills


def save_bills_to_file(
    bills: list[Bill],
    file_path: Path = BILLS_FILE,
) -> None:
    """Save bills to a JSON file."""
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    bill_data = [
        bill.to_dict()
        for bill in bills
    ]

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            bill_data,
            file,
            indent=4,
        )

    logger.debug(
        "Saved %d bill(s) to %s",
        len(bills),
        file_path,
    )