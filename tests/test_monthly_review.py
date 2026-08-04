"""Tests for AI-generated monthly financial reviews."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import anthropic
import httpx
import pytest

from src.core.exceptions import ExternalServiceError
from src.financial.coach import monthly_review
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority

USER_ID = 1


def build_current_snapshot() -> dict:
    return {
        "total_debt": Decimal("1000.00"),
        "net_worth": Decimal("5000.00"),
        "health_score": 80,
        "health_status": "Good",
        "goals": [
            {
                "id": 1,
                "name": "Emergency Fund",
                "target_amount": Decimal("10000.00"),
                "current_amount": Decimal("2500.00"),
            }
        ],
    }


def build_snapshot_record(
    days_ago: int,
    *,
    now: datetime,
    category_totals: dict | None = None,
) -> FinancialSnapshotRecord:
    return FinancialSnapshotRecord(
        timestamp=now - timedelta(days=days_ago),
        total_income=Decimal("5000.00"),
        total_expenses=Decimal("3000.00"),
        net_cash_flow=Decimal("2000.00"),
        total_account_balance=Decimal("4000.00"),
        total_goal_progress=Decimal("2500.00"),
        total_debt=Decimal("1000.00"),
        net_worth=Decimal("5000.00"),
        health_score=80,
        health_status="Good",
        category_totals=category_totals or {},
    )


def build_recommendation() -> Recommendation:
    return Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.DEBT,
        title="High Interest Debt",
        message="Card A has a high interest rate.",
        action="Prioritize this debt for repayment.",
        source_rule="HighInterestDebtRule",
    )


def test_generate_monthly_review_returns_no_history_status_with_empty_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No recorded snapshots should produce a no_history status without an LLM call."""
    monkeypatch.setattr(monthly_review, "get_history", lambda user_id: [])

    result = monthly_review.generate_monthly_review(USER_ID, build_current_snapshot())

    assert result["status"] == "no_history"


def test_generate_monthly_review_returns_insufficient_status_with_one_recent_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only one recent snapshot should produce an insufficient-data status."""
    now = datetime.now(timezone.utc)
    history = [build_snapshot_record(5, now=now)]

    monkeypatch.setattr(monthly_review, "get_history", lambda user_id: history)

    result = monthly_review.generate_monthly_review(
        USER_ID,
        build_current_snapshot(),
        now=now,
    )

    assert result["status"] == "insufficient_recent_history"
    assert "last_recorded_snapshot" in result


def test_generate_monthly_review_excludes_stale_snapshots_outside_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Old snapshots outside the review window shouldn't count toward the minimum."""
    now = datetime.now(timezone.utc)
    history = [
        build_snapshot_record(200, now=now),
        build_snapshot_record(150, now=now),
        build_snapshot_record(5, now=now),
    ]

    monkeypatch.setattr(monthly_review, "get_history", lambda user_id: history)

    result = monthly_review.generate_monthly_review(
        USER_ID,
        build_current_snapshot(),
        now=now,
    )

    assert result["status"] == "insufficient_recent_history"


def test_generate_monthly_review_ok_status_calls_llm_with_two_recent_snapshots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two recent snapshots should produce a full, LLM-narrated review."""
    now = datetime.now(timezone.utc)
    history = [
        build_snapshot_record(20, now=now),
        build_snapshot_record(1, now=now),
    ]

    monkeypatch.setattr(monthly_review, "get_history", lambda user_id: history)
    monkeypatch.setattr(
        monthly_review,
        "build_recommendations",
        lambda user_id, limit: [build_recommendation()],
    )
    monkeypatch.setattr(
        monthly_review,
        "_request_review",
        lambda prompt: {
            "overall_summary": "Overall summary.",
            "income_expenses_narrative": "Income narrative.",
            "cash_flow_narrative": "Cash flow narrative.",
            "debt_narrative": "Debt narrative.",
            "savings_narrative": "Savings narrative.",
            "goals_narrative": "Goals narrative.",
            "health_score_narrative": "Health score narrative.",
            "next_actions_narrative": "Next actions narrative.",
        },
    )

    result = monthly_review.generate_monthly_review(
        USER_ID,
        build_current_snapshot(),
        now=now,
    )

    assert result["status"] == "ok"
    assert result["overall_summary"] == "Overall summary."
    assert result["cash_flow"]["narrative"] == "Cash flow narrative."
    assert result["top_actions"][0]["title"] == "High Interest Debt"
    assert result["known_gaps"] == [monthly_review._CATEGORY_TREND_GAP_NOTE]
    assert result["category_trends"] == []


def test_generate_monthly_review_surfaces_real_category_trends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When category history exists, the gap note drops and trends are real."""
    now = datetime.now(timezone.utc)
    history = [
        build_snapshot_record(
            20, now=now, category_totals={"Food": Decimal("200.00")}
        ),
        build_snapshot_record(
            1, now=now, category_totals={"Food": Decimal("260.00")}
        ),
    ]

    monkeypatch.setattr(monthly_review, "get_history", lambda user_id: history)
    monkeypatch.setattr(
        monthly_review, "build_recommendations", lambda user_id, limit: [build_recommendation()]
    )
    monkeypatch.setattr(
        monthly_review,
        "_request_review",
        lambda prompt: {
            "overall_summary": "Overall summary.",
            "income_expenses_narrative": "Income narrative.",
            "cash_flow_narrative": "Cash flow narrative.",
            "debt_narrative": "Debt narrative.",
            "savings_narrative": "Savings narrative.",
            "goals_narrative": "Goals narrative.",
            "health_score_narrative": "Health score narrative.",
            "next_actions_narrative": "Next actions narrative.",
        },
    )

    result = monthly_review.generate_monthly_review(
        USER_ID,
        build_current_snapshot(),
        now=now,
    )

    assert result["known_gaps"] == []
    assert result["category_trends"] == [
        {"category": "Food", "change": Decimal("60.00"), "direction": "Increasing"}
    ]


def test_build_category_trends_filters_sorts_and_caps() -> None:
    changes = {
        "Food": Decimal("60.00"),
        "Utilities": Decimal("5.00"),  # below threshold, dropped
        "Entertainment": Decimal("-90.00"),
        "Housing": Decimal("30.00"),
        "Healthcare": Decimal("-200.00"),
    }

    trends = monthly_review._build_category_trends(changes)

    assert trends == [
        {"category": "Healthcare", "change": Decimal("-200.00"), "direction": "Decreasing"},
        {"category": "Entertainment", "change": Decimal("-90.00"), "direction": "Decreasing"},
        {"category": "Food", "change": Decimal("60.00"), "direction": "Increasing"},
    ]


def test_request_review_wraps_anthropic_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An Anthropic API failure should be wrapped in ExternalServiceError."""

    class FakeMessages:
        def create(self, **kwargs: object) -> None:
            raise anthropic.APIConnectionError(
                message="Connection error.",
                request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
            )

    class FakeClient:
        messages = FakeMessages()

    monkeypatch.setattr(monthly_review.ai_client, "get_client", lambda: FakeClient())

    with pytest.raises(ExternalServiceError):
        monthly_review._request_review("prompt")
