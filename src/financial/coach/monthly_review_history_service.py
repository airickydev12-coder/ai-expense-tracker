from datetime import datetime, timezone
from pathlib import Path

from src.core.config import DB_PATH
from src.core.logging import get_logger
from src.financial.coach.monthly_review_repository import (
    load_monthly_review_history_from_file,
    save_monthly_review_history_to_file,
)

logger = get_logger(__name__)

_reviews: list[dict] = []
_loaded_file_path: Path = DB_PATH


def load_monthly_review_history(
    file_path: Path = DB_PATH,
) -> None:
    """Load saved monthly reviews into application memory."""
    global _loaded_file_path

    _reviews.clear()
    _reviews.extend(load_monthly_review_history_from_file(file_path))

    _loaded_file_path = file_path


def save_monthly_review_history(
    file_path: Path | None = None,
) -> None:
    """Save all saved monthly reviews."""
    target_path = file_path if file_path is not None else _loaded_file_path

    save_monthly_review_history_to_file(_reviews, target_path)


def get_monthly_review_history() -> list[dict]:
    """Return a copy of all saved monthly reviews."""
    return _reviews.copy()


def record_monthly_review(
    review: dict,
    file_path: Path | None = None,
    *,
    now: datetime | None = None,
) -> dict:
    """
    Persist a completed ('ok' status) monthly review, stamped with the save time.

    Only ever called with a status == "ok" review -- degraded-status reviews
    (no_history / insufficient_recent_history) have nothing meaningful to
    save or later search.
    """
    stamped_review = {
        **review,
        "generated_at": (
            now if now is not None else datetime.now(timezone.utc)
        ).isoformat(),
    }

    _reviews.append(stamped_review)
    save_monthly_review_history(file_path)

    logger.info(
        "Recorded monthly review for period %s to %s",
        review.get("period_start"),
        review.get("period_end"),
    )

    return stamped_review


def clear_monthly_review_history() -> None:
    """Clear saved monthly reviews from application memory."""
    _reviews.clear()
