from decimal import Decimal

import pytest

from src.financial.scenarios.models import (
    ScenarioResult,
    ScenarioType,
)
from src.financial.scenarios.plan import (
    ScenarioPlanResult,
    build_cumulative_scenario_report,
)
from src.financial.scenarios.report import (
    build_scenario_comparison_report,
)
from src.financial.scenarios.scoring import (
    PlanRating,
    RiskLevel,
    ScoreComponent,
    SustainabilityLevel,
    classify_plan_rating,
    classify_risk_level,
    classify_sustainability,
    clamp_score,
    score_cash_flow,
    score_debt_improvement,
    score_financial_health,
    score_improvement_balance,
    score_net_worth,
    score_risk,
    score_savings_growth,
    score_scenario_plan,
    score_scenario_result,
)


def build_snapshot() -> dict:
    """Create a baseline financial snapshot."""
    return {
        "total_income": 5000,
        "total_expenses": 3000,
        "net_cash_flow": 2000,
        "total_account_balance": 8000,
        "total_goal_progress": 2500,
        "total_debt": 10000,
        "net_worth": 5000,
        "health_score": 70,
        "health_status": "Good",
    }


def build_positive_result() -> ScenarioResult:
    """Create a strongly positive scenario result."""
    original = build_snapshot()

    projected = {
        **original,
        "total_income": 5500,
        "total_expenses": 2800,
        "net_cash_flow": 2700,
        "total_account_balance": 11000,
        "total_goal_progress": 4000,
        "total_debt": 8000,
        "net_worth": 9000,
        "health_score": 82,
    }

    return ScenarioResult(
        scenario_type=ScenarioType.INCOME_INCREASE,
        name="Strong Growth Plan",
        description="",
        assumptions=[],
        original_snapshot=original,
        projected_snapshot=projected,
        impacts=[],
        benefits=[
            "Improved income and savings.",
        ],
        risks=[],
        recommendations=[],
    )


def build_risky_plan() -> ScenarioPlanResult:
    """Create a risky combined plan."""
    original = build_snapshot()

    projected = {
        **original,
        "net_cash_flow": -500,
        "total_account_balance": 6000,
        "total_debt": 11000,
        "net_worth": 2000,
        "health_score": 50,
    }

    return ScenarioPlanResult(
        name="Overcommitted Plan",
        description="",
        original_snapshot=original,
        projected_snapshot=projected,
        steps=[],
        cumulative_report=(
            build_cumulative_scenario_report(
                original,
                projected,
            )
        ),
        conflicts=[
            "Commitments exceed available cash flow.",
            "Projected cash flow is negative.",
        ],
        risks=[
            "The plan is not affordable.",
        ],
    )


def test_clamp_score():
    assert clamp_score(120) == 100
    assert clamp_score(-10) == 0
    assert clamp_score(75) == 75


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (95, PlanRating.EXCELLENT),
        (85, PlanRating.VERY_GOOD),
        (75, PlanRating.GOOD),
        (65, PlanRating.FAIR),
        (50, PlanRating.POOR),
    ],
)
def test_classify_plan_rating(
    score,
    expected,
):
    assert classify_plan_rating(score) == expected


def test_classify_risk_level():
    assert (
        classify_risk_level(
            risk_count=0,
            conflict_count=0,
            projected_cash_flow=Decimal("1000"),
        )
        == RiskLevel.LOW
    )

    assert (
        classify_risk_level(
            risk_count=2,
            conflict_count=0,
            projected_cash_flow=Decimal("1000"),
        )
        == RiskLevel.MODERATE
    )

    assert (
        classify_risk_level(
            risk_count=0,
            conflict_count=1,
            projected_cash_flow=Decimal("1000"),
        )
        == RiskLevel.HIGH
    )

    assert (
        classify_risk_level(
            risk_count=0,
            conflict_count=0,
            projected_cash_flow=Decimal("-1"),
        )
        == RiskLevel.CRITICAL
    )


def test_classify_sustainability():
    assert (
        classify_sustainability(
            projected_cash_flow=Decimal("2500"),
            original_cash_flow=Decimal("2000"),
            conflict_count=0,
        )
        == SustainabilityLevel.EXCELLENT
    )

    assert (
        classify_sustainability(
            projected_cash_flow=Decimal("1600"),
            original_cash_flow=Decimal("2000"),
            conflict_count=0,
        )
        == SustainabilityLevel.GOOD
    )

    assert (
        classify_sustainability(
            projected_cash_flow=Decimal("-100"),
            original_cash_flow=Decimal("2000"),
            conflict_count=0,
        )
        == SustainabilityLevel.POOR
    )


def test_score_component_create():
    component = ScoreComponent.create(
        name="Net Worth Growth",
        score=80,
        weight=0.25,
        explanation="Measures net-worth growth.",
    )

    assert component.score == 80
    assert component.weighted_score == 20


def test_score_net_worth():
    report = build_scenario_comparison_report(build_positive_result())

    assert score_net_worth(report) == 100


def test_score_cash_flow():
    report = build_scenario_comparison_report(build_positive_result())

    assert score_cash_flow(report) == 100


def test_score_debt_improvement():
    report = build_scenario_comparison_report(build_positive_result())

    assert score_debt_improvement(report) == 90


def test_score_savings_growth():
    report = build_scenario_comparison_report(build_positive_result())

    assert score_savings_growth(report) == 100


def test_score_financial_health():
    report = build_scenario_comparison_report(build_positive_result())

    score = score_financial_health(report)

    assert score > 80
    assert score <= 100


def test_score_improvement_balance():
    report = build_scenario_comparison_report(build_positive_result())

    assert score_improvement_balance(report) == 100


def test_score_risk():
    assert (
        score_risk(
            risk_count=0,
            conflict_count=0,
            projected_cash_flow=Decimal("2000"),
        )
        == 100
    )

    assert (
        score_risk(
            risk_count=2,
            conflict_count=1,
            projected_cash_flow=Decimal("1000"),
        )
        == 55
    )


def test_score_positive_scenario_result():
    score = score_scenario_result(build_positive_result())

    assert score.name == "Strong Growth Plan"
    assert score.overall_score >= 90
    assert score.rating == PlanRating.EXCELLENT
    assert score.risk_level == RiskLevel.LOW
    assert score.sustainability == SustainabilityLevel.EXCELLENT
    assert score.strengths
    assert not score.concerns


def test_score_risky_scenario_plan():
    score = score_scenario_plan(build_risky_plan())

    assert score.overall_score < 60
    assert score.rating == PlanRating.POOR
    assert score.risk_level == RiskLevel.CRITICAL
    assert score.sustainability == SustainabilityLevel.POOR
    assert score.concerns
    assert "not recommended" in (score.recommendation.lower())


def test_scenario_score_serialization():
    score = score_scenario_result(build_positive_result())

    data = score.to_dict()

    assert data["name"] == "Strong Growth Plan"
    assert data["rating"] == "Excellent"
    assert data["risk_level"] == "Low"
    assert len(data["components"]) == 7


def test_get_score_component():
    score = score_scenario_result(build_positive_result())

    component = score.get_component("net worth growth")

    assert component is not None
    assert component.weight == 0.25
