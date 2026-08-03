from pathlib import Path

from src.core.config import DB_PATH
from src.core.logging import get_logger
from src.financial.recommendations.history import RecommendationRecord
from src.financial.recommendations.history_repository import (
    load_recommendation_history_from_file,
    save_recommendation_history_to_file,
)
from src.financial.recommendations.lifecycle import (
    RecommendationLifecycleManager,
)
from src.financial.recommendations.models import Recommendation

logger = get_logger(__name__)

lifecycle_managers: dict[int, RecommendationLifecycleManager] = {}
_loaded_file_paths: dict[int, Path] = {}


def _get_manager(user_id: int) -> RecommendationLifecycleManager:
    """Return this user's lifecycle manager, creating an empty one if needed."""
    if user_id not in lifecycle_managers:
        lifecycle_managers[user_id] = RecommendationLifecycleManager()
    return lifecycle_managers[user_id]


def load_recommendation_history(
    user_id: int,
    file_path: Path = DB_PATH,
) -> None:
    """Load a user's persisted lifecycle records into memory."""
    records = load_recommendation_history_from_file(user_id, file_path)

    _get_manager(user_id).replace_records(records)
    _loaded_file_paths[user_id] = file_path


def save_recommendation_history(user_id: int, file_path: Path | None = None) -> None:
    """Save a user's current lifecycle records."""
    target_path = file_path if file_path is not None else _loaded_file_paths.get(user_id)

    if target_path is None:
        target_path = DB_PATH

    save_recommendation_history_to_file(
        _get_manager(user_id).get_records(),
        user_id,
        target_path,
    )


def get_recommendation_history(user_id: int) -> list[RecommendationRecord]:
    """Return all of a user's lifecycle records."""
    return _get_manager(user_id).get_records()


def get_recommendation_record(
    user_id: int,
    recommendation_key: str,
) -> RecommendationRecord | None:
    """Return one of a user's lifecycle records by key."""
    return _get_manager(user_id).get_record(recommendation_key)


def register_recommendation(
    user_id: int,
    recommendation: Recommendation,
) -> RecommendationRecord:
    """Register and persist a recommendation for this user."""
    manager = _get_manager(user_id)
    existing_record = manager.get_record(recommendation.key)

    record = manager.register(recommendation)

    if existing_record is None and user_id in _loaded_file_paths:
        save_recommendation_history(user_id)

    return record


def activate_recommendation(
    user_id: int,
    recommendation_key: str,
    note: str = "",
) -> RecommendationRecord | None:
    """Mark a recommendation active and persist it for this user."""
    record = _get_manager(user_id).activate(
        recommendation_key,
        note,
    )

    if record is not None and user_id in _loaded_file_paths:
        save_recommendation_history(user_id)
        logger.info(
            "Activated recommendation %s for user %d",
            recommendation_key,
            user_id,
        )

    return record


def complete_recommendation(
    user_id: int,
    recommendation_key: str,
    note: str = "",
) -> RecommendationRecord | None:
    """Mark a recommendation completed and persist it for this user."""
    record = _get_manager(user_id).complete(
        recommendation_key,
        note,
    )

    if record is not None and user_id in _loaded_file_paths:
        save_recommendation_history(user_id)
        logger.info(
            "Completed recommendation %s for user %d",
            recommendation_key,
            user_id,
        )

    return record


def dismiss_recommendation(
    user_id: int,
    recommendation_key: str,
    note: str = "",
) -> RecommendationRecord | None:
    """Mark a recommendation dismissed and persist it for this user."""
    record = _get_manager(user_id).dismiss(
        recommendation_key,
        note,
    )

    if record is not None and user_id in _loaded_file_paths:
        save_recommendation_history(user_id)
        logger.info(
            "Dismissed recommendation %s for user %d",
            recommendation_key,
            user_id,
        )

    return record


def suppress_recommendation(
    user_id: int,
    recommendation_key: str,
    note: str = "",
) -> RecommendationRecord | None:
    """Mark a recommendation suppressed and persist it for this user."""
    record = _get_manager(user_id).suppress(
        recommendation_key,
        note,
    )

    if record is not None and user_id in _loaded_file_paths:
        save_recommendation_history(user_id)
        logger.info(
            "Suppressed recommendation %s for user %d",
            recommendation_key,
            user_id,
        )

    return record


def filter_displayable_recommendations(
    user_id: int,
    recommendations: list[Recommendation],
) -> list[Recommendation]:
    """Filter recommendations according to a user's persisted lifecycle state."""
    manager = _get_manager(user_id)
    original_count = len(manager.get_records())

    displayable = manager.filter_displayable(recommendations)

    updated_count = len(manager.get_records())

    if updated_count != original_count and user_id in _loaded_file_paths:
        save_recommendation_history(user_id)

    return displayable


def reset_recommendation_history(user_id: int | None = None) -> None:
    """Clear lifecycle state and detach the loaded file.

    Clears every cached user's state when `user_id` is omitted (test
    convenience, matching the old module-level-singleton behavior), or just
    one user's state when given.
    """
    if user_id is None:
        lifecycle_managers.clear()
        _loaded_file_paths.clear()
        return

    lifecycle_managers.pop(user_id, None)
    _loaded_file_paths.pop(user_id, None)
