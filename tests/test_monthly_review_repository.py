from decimal import Decimal

import pytest

from src.financial.coach.monthly_review_repository import (
    load_monthly_review_history_from_file,
    save_monthly_review_history_to_file,
)


USER_ID = 1


def build_review() -> dict:
    """Create a complete, saved-shape monthly review."""
    return {
        "generated_at": "2026-08-02T12:00:00+00:00",
        "period_start": "2026-07-01T00:00:00+00:00",
        "period_end": "2026-08-01T00:00:00+00:00",
        "overall_summary": "Overall summary.",
        "income_vs_expenses": {
            "narrative": "Income narrative.",
            "income_change": Decimal("500.00"),
            "expense_change": Decimal("-100.00"),
        },
        "cash_flow": {
            "narrative": "Cash flow narrative.",
            "change": Decimal("600.00"),
            "direction": "Improving",
        },
        "debt_progress": {
            "narrative": "Debt narrative.",
            "total_debt": Decimal("1000.00"),
        },
        "savings_progress": {"narrative": "Savings narrative."},
        "goal_status": {"narrative": "Goals narrative."},
        "health_score": {
            "narrative": "Health score narrative.",
            "change": Decimal("5"),
            "direction": "Improving",
            "current_score": 80,
        },
        "top_actions": [
            {
                "key": "debt:high_interest_debt",
                "title": "High Interest Debt",
                "message": "Card A has a high interest rate.",
                "action": "Prioritize this debt for repayment.",
                "priority": "HIGH",
            }
        ],
        "known_gaps": ["Category-level spending trends aren't available."],
    }


def test_save_and_load_monthly_review_history(db_path):
    original_reviews = [build_review()]

    save_monthly_review_history_to_file(original_reviews, USER_ID, db_path)

    loaded_reviews = load_monthly_review_history_from_file(USER_ID, db_path)

    assert loaded_reviews == original_reviews


def test_save_and_load_preserves_decimal_values(db_path):
    """Decimal fields at arbitrary depth must round-trip as Decimal, not float/str."""
    save_monthly_review_history_to_file([build_review()], USER_ID, db_path)

    loaded = load_monthly_review_history_from_file(USER_ID, db_path)[0]

    assert loaded["income_vs_expenses"]["income_change"] == Decimal("500.00")
    assert isinstance(loaded["income_vs_expenses"]["income_change"], Decimal)
    assert loaded["debt_progress"]["total_debt"] == Decimal("1000.00")
    assert isinstance(loaded["debt_progress"]["total_debt"], Decimal)


def test_load_monthly_review_history_returns_empty_when_db_missing(tmp_path):
    db_path = tmp_path / "missing.db"

    assert load_monthly_review_history_from_file(USER_ID, db_path) == []


def test_load_monthly_review_history_rejects_invalid_database_file(tmp_path):
    db_path = tmp_path / "monthly_review_history.db"

    db_path.write_text("not a valid sqlite database", encoding="utf-8")

    with pytest.raises(ValueError, match="Failed to load monthly review history"):
        load_monthly_review_history_from_file(USER_ID, db_path)


def test_save_replaces_all_existing_rows(db_path):
    save_monthly_review_history_to_file([build_review()], USER_ID, db_path)

    second_review = {**build_review(), "overall_summary": "A newer summary."}
    save_monthly_review_history_to_file([second_review], USER_ID, db_path)

    loaded_reviews = load_monthly_review_history_from_file(USER_ID, db_path)

    assert len(loaded_reviews) == 1
    assert loaded_reviews[0]["overall_summary"] == "A newer summary."
