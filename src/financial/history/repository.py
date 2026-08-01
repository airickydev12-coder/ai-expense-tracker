import json
from pathlib import Path

from src.core.config import DATA_DIR
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.history.models import (
    FinancialSnapshotRecord,
)

logger = get_logger(__name__)

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
        logger.error(
            "Failed to parse financial history file %s: %s",
            file_path,
            error,
        )
        raise PersistenceError(
            "Financial history contains invalid JSON."
        ) from error

    if not isinstance(data, list):
        raise PersistenceError(
            "Financial history must be a JSON list."
        )

    records = [
        FinancialSnapshotRecord.from_dict(item)
        for item in data
    ]

    logger.debug(
        "Loaded %d financial history record(s) from %s",
        len(records),
        file_path,
    )

    return records


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

    logger.debug(
        "Saved %d financial history record(s) to %s",
        len(history),
        file_path,
    )