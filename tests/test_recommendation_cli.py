from datetime import datetime, timezone

from src.financial.recommendations.history import (
    RecommendationRecord,
)
from src.financial.recommendations.status import (
    RecommendationStatus,
)
from src.presentation import cli


def build_snapshot() -> dict:
    """Create a snapshot with one recommendation."""
    return {
        "recommendations": [
            {
                "key": "debt:high_interest_debt",
                "priority": "HIGH",
                "category": "Debt",
                "title": "High Interest Debt",
                "message": (
                    "You have high-interest debt."
                ),
                "action": "Prioritize repayment.",
            }
        ]
    }


def build_record() -> RecommendationRecord:
    """Create a lifecycle record for CLI tests."""
    timestamp = datetime.now(timezone.utc)

    return RecommendationRecord(
        recommendation_key=(
            "debt:high_interest_debt"
        ),
        status=RecommendationStatus.NEW,
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_select_recommendation_key(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    result = cli.select_recommendation_key(
        build_snapshot()["recommendations"]
    )

    assert result == (
        "debt:high_interest_debt"
    )


def test_select_recommendation_key_rejects_invalid_input(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "invalid",
    )

    result = cli.select_recommendation_key(
        build_snapshot()["recommendations"]
    )

    assert result is None


def test_select_history_record_key(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    result = cli.select_history_record_key(
        [build_record()]
    )

    assert result == (
        "debt:high_interest_debt"
    )


def test_manage_recommendations_completes_record(
    monkeypatch,
):
    captured: dict = {}

    inputs = iter(
        [
            "4",
            "1",
            "Debt paid off.",
            "7",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        cli,
        "build_current_financial_snapshot",
        build_snapshot,
    )

    monkeypatch.setattr(
        cli,
        "get_recommendation_history",
        lambda: [build_record()],
    )

    def fake_complete(
        recommendation_key: str,
        note: str = "",
    ):
        captured["key"] = recommendation_key
        captured["note"] = note
        return build_record()

    monkeypatch.setattr(
        cli,
        "complete_recommendation",
        fake_complete,
    )

    cli.manage_recommendations()

    assert captured["key"] == (
        "debt:high_interest_debt"
    )
    assert captured["note"] == (
        "Debt paid off."
    )


def test_manage_recommendations_dismisses_record(
    monkeypatch,
):
    captured: dict = {}

    inputs = iter(
        [
            "5",
            "1",
            "Not relevant now.",
            "7",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        cli,
        "build_current_financial_snapshot",
        build_snapshot,
    )

    monkeypatch.setattr(
        cli,
        "get_recommendation_history",
        lambda: [build_record()],
    )

    def fake_dismiss(
        recommendation_key: str,
        note: str = "",
    ):
        captured["key"] = recommendation_key
        captured["note"] = note
        return build_record()

    monkeypatch.setattr(
        cli,
        "dismiss_recommendation",
        fake_dismiss,
    )

    cli.manage_recommendations()

    assert captured["key"] == (
        "debt:high_interest_debt"
    )
    assert captured["note"] == (
        "Not relevant now."
    )