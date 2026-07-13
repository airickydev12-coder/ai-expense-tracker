from src.financial.recommendations.category import (
    RecommendationCategory,
)
from src.financial.recommendations.history_service import (
    activate_recommendation,
    complete_recommendation,
    dismiss_recommendation,
    filter_displayable_recommendations,
    get_recommendation_history,
    load_recommendation_history,
    register_recommendation,
    reset_recommendation_history,
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


def setup_function():
    """Reset recommendation history before each test."""
    reset_recommendation_history()


def teardown_function():
    """Reset recommendation history after each test."""
    reset_recommendation_history()


def build_recommendation() -> Recommendation:
    """Create a recommendation for persistence tests."""
    return Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.DEBT,
        title="High Interest Debt",
        message="You have high-interest debt.",
        action="Prioritize repayment.",
    )


def test_register_recommendation_is_persisted(
    tmp_path,
):
    file_path = (
        tmp_path / "recommendation_history.json"
    )

    load_recommendation_history(file_path)

    recommendation = build_recommendation()
    register_recommendation(recommendation)

    assert file_path.exists()
    assert len(get_recommendation_history()) == 1

    reset_recommendation_history()
    load_recommendation_history(file_path)

    records = get_recommendation_history()

    assert len(records) == 1
    assert records[0].recommendation_key == (
        recommendation.key
    )


def test_status_changes_are_persisted(
    tmp_path,
):
    file_path = (
        tmp_path / "recommendation_history.json"
    )

    load_recommendation_history(file_path)

    recommendation = build_recommendation()
    register_recommendation(recommendation)

    activate_recommendation(
        recommendation.key,
        note="User opened the recommendation.",
    )

    reset_recommendation_history()
    load_recommendation_history(file_path)

    record = get_recommendation_history()[0]

    assert record.status == RecommendationStatus.ACTIVE
    assert record.note == (
        "User opened the recommendation."
    )


def test_completed_recommendation_is_filtered(
    tmp_path,
):
    file_path = (
        tmp_path / "recommendation_history.json"
    )

    load_recommendation_history(file_path)

    recommendation = build_recommendation()

    register_recommendation(recommendation)
    complete_recommendation(
        recommendation.key,
        note="Debt paid off.",
    )

    results = filter_displayable_recommendations(
        [recommendation]
    )

    assert results == []


def test_dismissed_recommendation_stays_hidden_after_reload(
    tmp_path,
):
    file_path = (
        tmp_path / "recommendation_history.json"
    )

    load_recommendation_history(file_path)

    recommendation = build_recommendation()

    register_recommendation(recommendation)
    dismiss_recommendation(
        recommendation.key,
        note="Not relevant right now.",
    )

    reset_recommendation_history()
    load_recommendation_history(file_path)

    results = filter_displayable_recommendations(
        [recommendation]
    )

    assert results == []


def test_new_recommendation_is_registered_and_displayed(
    tmp_path,
):
    file_path = (
        tmp_path / "recommendation_history.json"
    )

    load_recommendation_history(file_path)

    recommendation = build_recommendation()

    results = filter_displayable_recommendations(
        [recommendation]
    )

    assert results == [recommendation]
    assert len(get_recommendation_history()) == 1
    assert get_recommendation_history()[0].status == (
        RecommendationStatus.NEW
    )