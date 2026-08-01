from pathlib import Path

from src.core.logging import get_logger
from src.financial.recommendations.history import RecommendationRecord
from src.financial.recommendations.history_repository import (
    RECOMMENDATION_HISTORY_FILE,
    load_recommendation_history_from_file,
    save_recommendation_history_to_file,
)
from src.financial.recommendations.lifecycle import (
    RecommendationLifecycleManager,
)
from src.financial.recommendations.models import Recommendation

logger = get_logger(__name__)

lifecycle_manager = RecommendationLifecycleManager()

_loaded_file_path: Path | None = None


def load_recommendation_history(
    file_path: Path = RECOMMENDATION_HISTORY_FILE,
) -> None:
    """Load persisted lifecycle records into memory."""
    global _loaded_file_path

    records = load_recommendation_history_from_file(
        file_path
    )

    lifecycle_manager.replace_records(records)
    _loaded_file_path = file_path


def save_recommendation_history(
    file_path: Path | None = None,
) -> None:
    """Save current lifecycle records."""
    target_path = (
        file_path
        if file_path is not None
        else _loaded_file_path
    )

    if target_path is None:
        target_path = RECOMMENDATION_HISTORY_FILE

    save_recommendation_history_to_file(
        lifecycle_manager.get_records(),
        target_path,
    )


def get_recommendation_history(
) -> list[RecommendationRecord]:
    """Return all lifecycle records."""
    return lifecycle_manager.get_records()


def get_recommendation_record(
    recommendation_key: str,
) -> RecommendationRecord | None:
    """Return one lifecycle record by key."""
    return lifecycle_manager.get_record(
        recommendation_key
    )


def register_recommendation(
    recommendation: Recommendation,
) -> RecommendationRecord:
    """Register and persist a recommendation."""
    existing_record = lifecycle_manager.get_record(
        recommendation.key
    )

    record = lifecycle_manager.register(
        recommendation
    )

    if (
        existing_record is None
        and _loaded_file_path is not None
    ):
        save_recommendation_history()

    return record


def activate_recommendation(
    recommendation_key: str,
    note: str = "",
) -> RecommendationRecord | None:
    """Mark a recommendation active and persist it."""
    record = lifecycle_manager.activate(
        recommendation_key,
        note,
    )

    if record is not None and _loaded_file_path is not None:
        save_recommendation_history()
        logger.info(
            "Activated recommendation %s",
            recommendation_key,
        )

    return record


def complete_recommendation(
    recommendation_key: str,
    note: str = "",
) -> RecommendationRecord | None:
    """Mark a recommendation completed and persist it."""
    record = lifecycle_manager.complete(
        recommendation_key,
        note,
    )

    if record is not None and _loaded_file_path is not None:
        save_recommendation_history()
        logger.info(
            "Completed recommendation %s",
            recommendation_key,
        )

    return record


def dismiss_recommendation(
    recommendation_key: str,
    note: str = "",
) -> RecommendationRecord | None:
    """Mark a recommendation dismissed and persist it."""
    record = lifecycle_manager.dismiss(
        recommendation_key,
        note,
    )

    if record is not None and _loaded_file_path is not None:
        save_recommendation_history()
        logger.info(
            "Dismissed recommendation %s",
            recommendation_key,
        )

    return record


def suppress_recommendation(
    recommendation_key: str,
    note: str = "",
) -> RecommendationRecord | None:
    """Mark a recommendation suppressed and persist it."""
    record = lifecycle_manager.suppress(
        recommendation_key,
        note,
    )

    if record is not None and _loaded_file_path is not None:
        save_recommendation_history()
        logger.info(
            "Suppressed recommendation %s",
            recommendation_key,
        )

    return record


def filter_displayable_recommendations(
    recommendations: list[Recommendation],
) -> list[Recommendation]:
    """Filter recommendations according to persisted lifecycle state."""
    original_count = len(
        lifecycle_manager.get_records()
    )

    displayable = lifecycle_manager.filter_displayable(
        recommendations
    )

    updated_count = len(
        lifecycle_manager.get_records()
    )

    if (
        updated_count != original_count
        and _loaded_file_path is not None
    ):
        save_recommendation_history()

    return displayable


def reset_recommendation_history() -> None:
    """Clear lifecycle state and detach the loaded file."""
    global _loaded_file_path

    lifecycle_manager.clear()
    _loaded_file_path = None