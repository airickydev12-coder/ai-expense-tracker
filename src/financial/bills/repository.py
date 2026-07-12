import json
from pathlib import Path

from src.core.config import DATA_DIR
from src.financial.bills.models import Bill


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
        raise ValueError(
            f"Bill data file contains invalid JSON: {file_path}"
        ) from error

    if not isinstance(raw_data, list):
        raise ValueError("Bill data must be stored as a JSON list.")

    return [
        Bill.from_dict(bill_data)
        for bill_data in raw_data
    ]


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