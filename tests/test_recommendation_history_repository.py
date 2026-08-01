import pytest

from src.financial.recommendations.history import (
    RecommendationRecord,
)
from src.financial.recommendations.history_repository import (
    load_recommendation_history_from_file,
    save_recommendation_history_to_file,
)
from src.financial.recommendations.status import (
    RecommendationStatus,
)


def test_save_and_load_recommendation_history(
    db_path,
):
    records = [
        RecommendationRecord.create(
            recommendation_key=("debt:high_interest_debt"),
            status=RecommendationStatus.ACTIVE,
            note="User is reviewing this debt.",
        ),
        RecommendationRecord.create(
            recommendation_key=("budget:budget_overrun"),
            status=RecommendationStatus.COMPLETED,
            note="Budget was corrected.",
        ),
    ]

    save_recommendation_history_to_file(
        records,
        db_path,
    )

    loaded_records = load_recommendation_history_from_file(db_path)

    assert len(loaded_records) == 2
    assert loaded_records[0].recommendation_key == ("budget:budget_overrun")
    assert loaded_records[0].status == (RecommendationStatus.COMPLETED)
    assert loaded_records[1].status == (RecommendationStatus.ACTIVE)


def test_load_history_returns_empty_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing.db"

    assert load_recommendation_history_from_file(db_path) == []


def test_save_history_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "recommendation_history.db"

    save_recommendation_history_to_file(
        [],
        db_path,
    )

    assert db_path.exists()


def test_load_history_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "history.db"

    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load recommendation history",
    ):
        load_recommendation_history_from_file(db_path)
