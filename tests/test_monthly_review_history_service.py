from datetime import datetime, timezone

from src.financial.coach.monthly_review_history_service import (
    clear_monthly_review_history,
    get_monthly_review_history,
    load_monthly_review_history,
    record_monthly_review,
)

USER_ID = 1


def setup_function():
    """Clear saved reviews before each service test."""
    clear_monthly_review_history()


def teardown_function():
    """Clear saved reviews after each service test."""
    clear_monthly_review_history()


def build_ok_review() -> dict:
    """Create a status == 'ok' review, as generate_monthly_review() returns it."""
    return {
        "status": "ok",
        "period_start": "2026-07-01T00:00:00+00:00",
        "period_end": "2026-08-01T00:00:00+00:00",
        "overall_summary": "Overall summary.",
    }


def test_record_monthly_review_stamps_generated_at(tmp_path):
    file_path = tmp_path / "monthly_review_history.db"

    load_monthly_review_history(USER_ID, file_path)

    stamped = record_monthly_review(
        USER_ID,
        build_ok_review(),
        file_path=file_path,
        now=datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc),
    )

    assert stamped["generated_at"] == "2026-08-02T12:00:00+00:00"
    assert stamped["overall_summary"] == "Overall summary."
    assert len(get_monthly_review_history(USER_ID)) == 1
    assert file_path.exists()


def test_record_monthly_review_is_restored_after_reload(tmp_path):
    file_path = tmp_path / "monthly_review_history.db"

    load_monthly_review_history(USER_ID, file_path)
    record_monthly_review(USER_ID, build_ok_review(), file_path=file_path)

    clear_monthly_review_history()
    assert get_monthly_review_history(USER_ID) == []

    load_monthly_review_history(USER_ID, file_path)

    reviews = get_monthly_review_history(USER_ID)

    assert len(reviews) == 1
    assert reviews[0]["overall_summary"] == "Overall summary."


def test_get_monthly_review_history_returns_copy(tmp_path):
    file_path = tmp_path / "monthly_review_history.db"

    load_monthly_review_history(USER_ID, file_path)
    record_monthly_review(USER_ID, build_ok_review(), file_path=file_path)

    returned_reviews = get_monthly_review_history(USER_ID)
    returned_reviews.clear()

    assert len(get_monthly_review_history(USER_ID)) == 1
