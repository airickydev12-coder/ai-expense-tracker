import json
from pathlib import Path

from src.core.config import DATA_DIR
from src.financial.recommendations.history import RecommendationRecord


RECOMMENDATION_HISTORY_FILE = (
    DATA_DIR / "recommendation_history.json"
)


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
        raise ValueError(
            "Recommendation history file contains invalid JSON: "
            f"{file_path}"
        ) from error

    if not isinstance(raw_data, list):
        raise ValueError(
            "Recommendation history must be stored as a JSON list."
        )

    return [
        RecommendationRecord.from_dict(record_data)
        for record_data in raw_data
    ]


def save_recommendation_history_to_file(
    records: list[RecommendationRecord],
    file_path: Path = RECOMMENDATION_HISTORY_FILE,
) -> None:
    """Save recommendation lifecycle records to JSON."""
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    record_data = [
        record.to_dict()
        for record in records
    ]

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            record_data,
            file,
            indent=4,
        )