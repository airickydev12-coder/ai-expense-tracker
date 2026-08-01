from datetime import datetime, timezone

from src.financial.coach.coaching import (
    CoachingSession,
)
from src.financial.coach.insights import (
    FinancialCoachInsight,
    InsightSeverity,
)
from src.financial.coach.models import (
    AdviceExplanation,
    CoachingAdvice,
    CoachingCategory,
    CoachingPriority,
)
from src.presentation import coach_views


def build_session() -> CoachingSession:
    """Create a coaching session for view tests."""
    advice = CoachingAdvice(
        key="optimizer:income:test",
        title="Increase Income by 10%",
        message=("This scenario is ranked first."),
        action=("Direct part of the additional " "income to savings."),
        reason=("It improves cash flow and net worth."),
        priority=CoachingPriority.HIGH,
        category=CoachingCategory.INCOME,
        expected_impact=("Projected effects include net worth " "+6,000.00."),
        source_scenario="Increase Income by 10%",
        score=92,
    )

    explanation = AdviceExplanation(
        advice_key=advice.key,
        summary=("Increase Income by 10% is recommended."),
        why_it_matters=("Higher income strengthens financial capacity."),
        projected_effects=[
            "Net Worth changes by +6,000.00.",
            "Net Cash Flow changes by +500.00.",
        ],
        assumptions=[
            "Increase Percentage: 10",
        ],
        risks=[],
    )

    insights = [
        FinancialCoachInsight(
            key="cash_flow:positive",
            title="Positive Monthly Cash Flow",
            message=("The current monthly surplus is " "$2,000.00."),
            category=CoachingCategory.CASH_FLOW,
            severity=InsightSeverity.POSITIVE,
            action=("Assign the surplus deliberately."),
        ),
        FinancialCoachInsight(
            key="savings:emergency_fund",
            title="Emergency Fund Below Target",
            message=("Available balances cover two months " "of expenses."),
            category=CoachingCategory.SAVINGS,
            severity=InsightSeverity.WARNING,
            action=("Build reserves toward three months."),
        ),
    ]

    return CoachingSession(
        generated_at=datetime(
            2026,
            7,
            16,
            14,
            30,
            tzinfo=timezone.utc,
        ),
        financial_health_score=72,
        financial_health_status="Good",
        summary=("Financial health is Good at 72/100."),
        _advice=(advice,),
        _explanations=(explanation,),
        _insights=tuple(insights),
        _next_steps=(
            "Direct part of the additional income to savings.",
            "Build reserves toward three months.",
        ),
        _warnings=("Available balances cover only two months " "of expenses.",),
    )


def test_display_coaching_summary(
    capsys,
):
    coach_views.display_coaching_summary(build_session())

    output = capsys.readouterr().out

    assert "Financial Health" in output
    assert "72/100" in output
    assert "Good" in output
    assert "2026-07-16 14:30" in output
    assert "Summary" in output


def test_display_top_advice(
    capsys,
):
    coach_views.display_top_advice(build_session())

    output = capsys.readouterr().out

    assert "Top Recommendation" in output
    assert "Increase Income by 10%" in output
    assert "High" in output
    assert "Income" in output
    assert "92.00/100" in output
    assert "Why This Matters" in output
    assert "Projected Effects" in output
    assert "Assumptions" in output


def test_display_coaching_insights(
    capsys,
):
    coach_views.display_coaching_insights(build_session())

    output = capsys.readouterr().out

    assert "Key Financial Insights" in output
    assert "Positive Monthly Cash Flow" in output
    assert "Emergency Fund Below Target" in output
    assert "[Positive]" in output
    assert "[Warning]" in output


def test_display_next_steps(
    capsys,
):
    coach_views.display_next_steps(build_session())

    output = capsys.readouterr().out

    assert "Recommended Next Steps" in output
    assert "1. Direct part" in output
    assert "2. Build reserves" in output


def test_display_coaching_warnings(
    capsys,
):
    coach_views.display_coaching_warnings(build_session())

    output = capsys.readouterr().out

    assert "Important Considerations" in output
    assert "only two months" in output


def test_display_complete_coaching_session(
    capsys,
):
    coach_views.display_complete_coaching_session(build_session())

    output = capsys.readouterr().out

    assert "AI Financial Coach" in output
    assert "Financial Health" in output
    assert "Top Recommendation" in output
    assert "Key Financial Insights" in output
    assert "Recommended Next Steps" in output
    assert "Important Considerations" in output


def test_display_top_advice_when_empty(
    capsys,
):
    session = CoachingSession(
        generated_at=datetime.now(timezone.utc),
        financial_health_score=80,
        financial_health_status="Good",
        summary="No optimizer advice.",
        _advice=(),
        _explanations=(),
        _insights=(),
        _next_steps=(),
        _warnings=(),
    )

    coach_views.display_top_advice(session)

    output = capsys.readouterr().out

    assert "No optimizer recommendation is available." in output
