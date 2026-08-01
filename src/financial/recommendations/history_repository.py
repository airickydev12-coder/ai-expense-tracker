import json
from pathlib import Path

from src.core.config import RECOMMENDATION_HISTORY_FILE
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.recommendations.history import RecommendationRecord

logger = get_logger(__name__)


def load_recommendation_history_from_file(
    file_path: Path = RECOMMENDATION_HISTORY_FILE,
) -> list[RecommendationRecord]:
    """Load recommendation lifecycle records from JSON."""
    if not file_path.exists():
        return []

    try:
        with file_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError as error:
        logger.error(
            "Failed to parse recommendation history file %s: %s",
            file_path,
            error,
        )
        raise PersistenceError(
            "Recommendation history file contains invalid JSON: " f"{file_path}"
        ) from error

    if not isinstance(raw_data, list):
        raise PersistenceError("Recommendation history must be stored as a JSON list.")

    records = [RecommendationRecord.from_dict(record_data) for record_data in raw_data]

    logger.debug(
        "Loaded %d recommendation history record(s) from %s",
        len(records),
        file_path,
    )

    return records


def save_recommendation_history_to_file(
    records: list[RecommendationRecord],
    file_path: Path = RECOMMENDATION_HISTORY_FILE,
) -> None:
    """Save recommendation lifecycle records to JSON."""
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    record_data = [record.to_dict() for record in records]

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            record_data,
            file,
            indent=4,
        )

    logger.debug(
        "Saved %d recommendation history record(s) to %s",
        len(records),
        file_path,
    )
