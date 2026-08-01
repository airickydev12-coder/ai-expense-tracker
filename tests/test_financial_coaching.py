from datetime import datetime, timezone

import pytest

from src.financial.coach.coaching import (
    build_coaching_session,
)
from src.financial.coach.insights import (
    InsightSeverity,
)
from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.optimizer import (
    OptimizationResult,
)
from src.financial.scenarios.ranking import (
    ScenarioRankingMetric,
    rank_scenarios,
)


def build_snapshot() -> dict:
    """Create a snapshot for coaching-session tests."""
    return {
        "total_income": 5000,
        "total_expenses": 3000,
        "net_cash_flow": 2000,
        "total_account_balance": 9000,
        "total_goal_progress": 2500,
        "total_debt": 12000,
        "net_worth": -500,
        "health_score": 68,
        "health_status": "Fair",
        "category_totals": {
            "Housing": 1500,
            "Food": 600,
        },
    }


def build_scenario_result() -> ScenarioResult:
    """Create a scenario result for coaching tests."""
    original = build_snapshot()

    return ScenarioResult(
        scenario_type=(ScenarioType.INCOME_INCREASE),
        name="Increase Income by 10%",
        description="",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot={
            **original,
            "total_income": 5500,
            "net_cash_flow": 2500,
            "total_account_balance": 15000,
            "net_worth": 5500,
            "health_score": 80,
        },
        impacts=[],
        recommendations=["Direct part of the additional income to savings."],
    )


def build_optimization_result() -> OptimizationResult:
    """Create an optimization result for coaching tests."""
    result = build_scenario_result()

    return OptimizationResult(
        snapshot=build_snapshot(),
        candidates=[],
        successful_results=[
            result,
        ],
        ranked_scenarios=rank_scenarios(
            [result],
            ScenarioRankingMetric.OVERALL,
        ),
        failures=[],
        ranking_metric=(ScenarioRankingMetric.OVERALL),
    )


def test_build_coaching_session():
    generated_at = datetime(
        2026,
        7,
        16,
        12,
        0,
        tzinfo=timezone.utc,
    )

    session = build_coaching_session(
        build_snapshot(),
        build_optimization_result(),
        generated_at=generated_at,
    )

    assert session.generated_at == generated_at
    assert session.financial_health_score == 68
    assert session.financial_health_status == "Fair"
    assert session.summary
    assert len(session.advice) == 1
    assert len(session.explanations) == 1
    assert session.insights
    assert session.next_steps
    assert session.top_advice is not None


def test_session_matches_advice_to_explanation():
    session = build_coaching_session(
        build_snapshot(),
        build_optimization_result(),
    )

    top_advice = session.top_advice

    assert top_advice is not None

    explanation = session.get_explanation(top_advice.key)

    assert explanation is not None
    assert explanation.advice_key == top_advice.key


def test_session_builds_warning_insights():
    snapshot = build_snapshot()
    snapshot["net_cash_flow"] = -500

    session = build_coaching_session(
        snapshot,
        build_optimization_result(),
    )

    assert session.critical_insights
    assert any(
        insight.severity == InsightSeverity.CRITICAL for insight in session.insights
    )
    assert session.warnings


def test_coaching_session_respects_advice_limit():
    session = build_coaching_session(
        build_snapshot(),
        build_optimization_result(),
        advice_limit=0,
    )

    assert session.advice == []
    assert session.explanations == []
    assert session.top_advice is None


def test_coaching_session_rejects_negative_advice_limit():
    with pytest.raises(
        ValueError,
        match="Advice limit cannot be negative",
    ):
        build_coaching_session(
            build_snapshot(),
            build_optimization_result(),
            advice_limit=-1,
        )


def test_coaching_session_rejects_invalid_step_limit():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        build_coaching_session(
            build_snapshot(),
            build_optimization_result(),
            next_step_limit=0,
        )


def test_coaching_session_serialization():
    session = build_coaching_session(
        build_snapshot(),
        build_optimization_result(),
    )

    data = session.to_dict()

    assert data["financial_health_score"] == 68
    assert data["financial_health_status"] == "Fair"
    assert data["advice"]
    assert data["explanations"]
    assert data["insights"]
    assert data["next_steps"]


def test_coaching_session_copies_collections():
    session = build_coaching_session(
        build_snapshot(),
        build_optimization_result(),
    )

    advice = session.advice
    advice.clear()

    assert session.advice
