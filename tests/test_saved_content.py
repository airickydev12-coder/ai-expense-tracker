"""Tests for pragmatic personal-RAG retrieval over saved reviews and scenarios."""

from decimal import Decimal

from src.financial.coach import saved_content
from src.financial.scenarios.models import (
    ScenarioImpact,
    ScenarioResult,
    ScenarioType,
)


def build_review(generated_at: str, summary: str) -> dict:
    return {
        "generated_at": generated_at,
        "period_start": "2026-07-01T00:00:00+00:00",
        "period_end": "2026-08-01T00:00:00+00:00",
        "overall_summary": summary,
    }


def build_scenario(name: str, description: str) -> ScenarioResult:
    return ScenarioResult(
        scenario_type=ScenarioType.ADDITIONAL_SAVINGS,
        name=name,
        description=description,
        assumptions=[],
        original_snapshot={"total_income": Decimal("5000.00")},
        projected_snapshot={"total_income": Decimal("5000.00")},
        impacts=[
            ScenarioImpact.create(
                metric="Net Worth",
                original_value=Decimal("500.00"),
                projected_value=Decimal("800.00"),
            )
        ],
    )


def test_search_monthly_reviews_orders_by_recency(monkeypatch) -> None:
    older = build_review("2026-06-01T00:00:00+00:00", "Older review.")
    newer = build_review("2026-07-01T00:00:00+00:00", "Newer review.")

    monkeypatch.setattr(saved_content, "get_monthly_review_history", lambda: [older, newer])

    results = saved_content.search_monthly_reviews()

    assert results == [newer, older]


def test_search_monthly_reviews_filters_by_keyword(monkeypatch) -> None:
    emergency = build_review("2026-06-01T00:00:00+00:00", "Emergency fund needs attention.")
    unrelated = build_review("2026-07-01T00:00:00+00:00", "Debt is under control.")

    monkeypatch.setattr(
        saved_content, "get_monthly_review_history", lambda: [emergency, unrelated]
    )

    results = saved_content.search_monthly_reviews(query="emergency fund")

    assert results == [emergency]


def test_search_monthly_reviews_respects_limit(monkeypatch) -> None:
    reviews = [
        build_review(f"2026-0{i}-01T00:00:00+00:00", f"Review {i}") for i in range(1, 5)
    ]

    monkeypatch.setattr(saved_content, "get_monthly_review_history", lambda: reviews)

    results = saved_content.search_monthly_reviews(limit=2)

    assert len(results) == 2


def test_search_saved_scenarios_filters_by_keyword(monkeypatch) -> None:
    savings_scenario = build_scenario("Save More", "Model saving an extra $300 per month.")
    debt_scenario = build_scenario("Pay Off Card A", "Model paying extra toward Card A.")

    class FakeWorkspace:
        def get_results(self) -> list[ScenarioResult]:
            return [savings_scenario, debt_scenario]

    monkeypatch.setattr(saved_content, "get_scenario_workspace", lambda: FakeWorkspace())

    results = saved_content.search_saved_scenarios(query="Card A")

    assert len(results) == 1
    assert results[0]["name"] == "Pay Off Card A"


def test_search_saved_scenarios_returns_all_when_no_query(monkeypatch) -> None:
    class FakeWorkspace:
        def get_results(self) -> list[ScenarioResult]:
            return [build_scenario("Save More", "Model saving more.")]

    monkeypatch.setattr(saved_content, "get_scenario_workspace", lambda: FakeWorkspace())

    results = saved_content.search_saved_scenarios()

    assert len(results) == 1


def test_search_saved_content_combines_both_sources(monkeypatch) -> None:
    monkeypatch.setattr(saved_content, "get_monthly_review_history", lambda: [])

    class FakeWorkspace:
        def get_results(self) -> list[ScenarioResult]:
            return []

    monkeypatch.setattr(saved_content, "get_scenario_workspace", lambda: FakeWorkspace())

    result = saved_content.search_saved_content()

    assert result == {"monthly_reviews": [], "scenarios": []}
