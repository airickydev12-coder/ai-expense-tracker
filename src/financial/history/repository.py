import json
from pathlib import Path

from src.core.config import DATA_DIR
from src.financial.history.models import (
    FinancialSnapshotRecord,
)

HISTORY_FILE = (
    DATA_DIR /
    "financial_history.json"
)


def load_history_from_file(
    file_path: Path = HISTORY_FILE,
) -> list[FinancialSnapshotRecord]:
    """Load historical financial snapshots."""

    if not file_path.exists():
        return []

    try:
        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            "Financial history contains invalid JSON."
        ) from error

    if not isinstance(data, list):
        raise ValueError(
            "Financial history must be a JSON list."
        )

    return [
        FinancialSnapshotRecord.from_dict(item)
        for item in data
    ]


def save_history_to_file(
    history: list[FinancialSnapshotRecord],
    file_path: Path = HISTORY_FILE,
) -> None:
    """Save financial history."""

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            [
                snapshot.to_dict()
                for snapshot in history
            ],
            file,
            indent=4,
        )