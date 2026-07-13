import json

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
    tmp_path,
):
    file_path = (
        tmp_path / "recommendation_history.json"
    )

    records = [
        RecommendationRecord.create(
            recommendation_key=(
                "debt:high_interest_debt"
            ),
            status=RecommendationStatus.ACTIVE,
            note="User is reviewing this debt.",
        ),
        RecommendationRecord.create(
            recommendation_key=(
                "budget:budget_overrun"
            ),
            status=RecommendationStatus.COMPLETED,
            note="Budget was corrected.",
        ),
    ]

    save_recommendation_history_to_file(
        records,
        file_path,
    )

    loaded_records = (
        load_recommendation_history_from_file(
            file_path
        )
    )

    assert len(loaded_records) == 2
    assert loaded_records[0].recommendation_key == (
        "debt:high_interest_debt"
    )
    assert loaded_records[0].status == (
        RecommendationStatus.ACTIVE
    )
    assert loaded_records[1].status == (
        RecommendationStatus.COMPLETED
    )


def test_load_history_returns_empty_when_missing(
    tmp_path,
):
    file_path = tmp_path / "missing.json"

    assert (
        load_recommendation_history_from_file(
            file_path
        )
        == []
    )


def test_save_history_creates_parent_directory(
    tmp_path,
):
    file_path = (
        tmp_path
        / "nested"
        / "data"
        / "recommendation_history.json"
    )

    save_recommendation_history_to_file(
        [],
        file_path,
    )

    assert file_path.exists()


def test_load_history_rejects_invalid_json(
    tmp_path,
):
    file_path = tmp_path / "history.json"

    file_path.write_text(
        "not valid json",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="invalid JSON",
    ):
        load_recommendation_history_from_file(
            file_path
        )


def test_load_history_rejects_non_list_json(
    tmp_path,
):
    file_path = tmp_path / "history.json"

    file_path.write_text(
        json.dumps(
            {
                "recommendation_key": "test:key",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="JSON list",
    ):
        load_recommendation_history_from_file(
            file_path
        )