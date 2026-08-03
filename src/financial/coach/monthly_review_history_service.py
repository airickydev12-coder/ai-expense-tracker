from datetime import datetime, timezone
from pathlib import Path

from src.core.config import DB_PATH
from src.core.logging import get_logger
from src.financial.coach.monthly_review_repository import (
    load_monthly_review_history_from_file,
    save_monthly_review_history_to_file,
)

logger = get_logger(__name__)

_reviews: dict[int, list[dict]] = {}


def _ensure_loaded(user_id: int, db_path: Path = DB_PATH) -> None:
    """Lazily load a user's monthly reviews into the cache on first access."""
    if user_id not in _reviews:
        _reviews[user_id] = load_monthly_review_history_from_file(user_id, db_path)


def load_monthly_review_history(
    user_id: int,
    file_path: Path = DB_PATH,
) -> None:
    """Load a user's saved monthly reviews into application memory."""
    _reviews[user_id] = load_monthly_review_history_from_file(user_id, file_path)


def save_monthly_review_history(user_id: int, file_path: Path = DB_PATH) -> None:
    """Save all of a user's saved monthly reviews."""
    save_monthly_review_history_to_file(_reviews[user_id], user_id, file_path)


def get_monthly_review_history(user_id: int, db_path: Path = DB_PATH) -> list[dict]:
    """Return a copy of all of a user's saved monthly reviews."""
    _ensure_loaded(user_id, db_path)
    return _reviews[user_id].copy()


def record_monthly_review(
    user_id: int,
    review: dict,
    file_path: Path = DB_PATH,
    *,
    now: datetime | None = None,
) -> dict:
    """
    Persist a completed ('ok' status) monthly review, stamped with the save time.

    Only ever called with a status == "ok" review -- degraded-status reviews
    (no_history / insufficient_recent_history) have nothing meaningful to
    save or later search.
    """
    _ensure_loaded(user_id, file_path)

    stamped_review = {
        **review,
        "generated_at": (
            now if now is not None else datetime.now(timezone.utc)
        ).isoformat(),
    }

    _reviews[user_id].append(stamped_review)
    save_monthly_review_history(user_id, file_path)

    logger.info(
        "Recorded monthly review for period %s to %s for user %d",
        review.get("period_start"),
        review.get("period_end"),
        user_id,
    )

    return stamped_review


def clear_monthly_review_history(user_id: int | None = None) -> None:
    """Clear saved monthly reviews from application memory.

    Clears every cached user's reviews when `user_id` is omitted (test
    convenience, matching the old module-level-list behavior), or just one
    user's reviews when given.
    """
    if user_id is None:
        _reviews.clear()
        return

    _reviews[user_id] = []
