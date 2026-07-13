from datetime import datetime, timezone

import pytest

from src.financial.recommendations.category import (
    RecommendationCategory,
)
from src.financial.recommendations.history import (
    RecommendationRecord,
)
from src.financial.recommendations.lifecycle import (
    RecommendationLifecycleManager,
)
from src.financial.recommendations.models import (
    Recommendation,
)
from src.financial.recommendations.priority import (
    RecommendationPriority,
)
from src.financial.recommendations.status import (
    RecommendationStatus,
)


def build_recommendation() -> Recommendation:
    """Create a recommendation for lifecycle tests."""
    return Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.DEBT,
        title="High Interest Debt",
        message="You have high-interest debt.",
        action="Prioritize repayment.",
    )


def test_recommendation_record_create():
    record = RecommendationRecord.create(
        recommendation_key="debt:high_interest_debt"
    )

    assert record.recommendation_key == (
        "debt:high_interest_debt"
    )
    assert record.status == RecommendationStatus.NEW
    assert record.created_at == record.updated_at


def test_recommendation_record_rejects_empty_key():
    timestamp = datetime.now(timezone.utc)

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        RecommendationRecord(
            recommendation_key=" ",
            status=RecommendationStatus.NEW,
            created_at=timestamp,
            updated_at=timestamp,
        )


def test_recommendation_record_serialization():
    record = RecommendationRecord.create(
        recommendation_key="debt:high_interest_debt",
        note="Review monthly.",
    )

    restored_record = RecommendationRecord.from_dict(
        record.to_dict()
    )

    assert restored_record.recommendation_key == (
        record.recommendation_key
    )
    assert restored_record.status == record.status
    assert restored_record.note == "Review monthly."


def test_register_recommendation():
    manager = RecommendationLifecycleManager()
    recommendation = build_recommendation()

    record = manager.register(recommendation)

    assert record.recommendation_key == recommendation.key
    assert record.status == RecommendationStatus.NEW
    assert len(manager.get_records()) == 1


def test_register_does_not_create_duplicate_record():
    manager = RecommendationLifecycleManager()
    recommendation = build_recommendation()

    first_record = manager.register(recommendation)
    second_record = manager.register(recommendation)

    assert first_record is second_record
    assert len(manager.get_records()) == 1


def test_activate_recommendation():
    manager = RecommendationLifecycleManager()
    recommendation = build_recommendation()

    manager.register(recommendation)

    record = manager.activate(
        recommendation.key,
        note="User opened recommendation.",
    )

    assert record is not None
    assert record.status == RecommendationStatus.ACTIVE
    assert record.note == "User opened recommendation."


def test_complete_recommendation():
    manager = RecommendationLifecycleManager()
    recommendation = build_recommendation()

    manager.register(recommendation)

    record = manager.complete(
        recommendation.key,
        note="Debt was paid off.",
    )

    assert record is not None
    assert record.status == RecommendationStatus.COMPLETED
    assert manager.should_display(
        recommendation.key
    ) is False


def test_dismiss_recommendation():
    manager = RecommendationLifecycleManager()
    recommendation = build_recommendation()

    manager.register(recommendation)

    record = manager.dismiss(
        recommendation.key,
        note="User dismissed advice.",
    )

    assert record is not None
    assert record.status == RecommendationStatus.DISMISSED
    assert manager.should_display(
        recommendation.key
    ) is False


def test_suppress_recommendation():
    manager = RecommendationLifecycleManager()
    recommendation = build_recommendation()

    manager.register(recommendation)

    record = manager.suppress(
        recommendation.key,
        note="Temporarily suppressed.",
    )

    assert record is not None
    assert record.status == RecommendationStatus.SUPPRESSED
    assert manager.should_display(
        recommendation.key
    ) is False


def test_status_update_returns_none_for_missing_record():
    manager = RecommendationLifecycleManager()

    assert manager.activate("missing:key") is None
    assert manager.complete("missing:key") is None
    assert manager.dismiss("missing:key") is None
    assert manager.suppress("missing:key") is None


def test_should_display_unknown_recommendation():
    manager = RecommendationLifecycleManager()

    assert manager.should_display(
        "unknown:key"
    ) is True


def test_filter_displayable_registers_new_recommendations():
    manager = RecommendationLifecycleManager()
    recommendation = build_recommendation()

    results = manager.filter_displayable(
        [recommendation]
    )

    assert results == [recommendation]
    assert manager.get_record(
        recommendation.key
    ) is not None


def test_filter_displayable_excludes_completed_recommendation():
    manager = RecommendationLifecycleManager()
    recommendation = build_recommendation()

    manager.register(recommendation)
    manager.complete(recommendation.key)

    results = manager.filter_displayable(
        [recommendation]
    )

    assert results == []


def test_clear_removes_all_records():
    manager = RecommendationLifecycleManager()
    manager.register(build_recommendation())

    manager.clear()

    assert manager.get_records() == []