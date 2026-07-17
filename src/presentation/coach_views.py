from src.financial.coach.coaching import (
    CoachingSession,
)
from src.financial.coach.insights import (
    InsightSeverity,
)


def _format_generated_at(
    session: CoachingSession,
) -> str:
    """Format the coaching-session timestamp for users."""
    return session.generated_at.strftime("%Y-%m-%d %H:%M")


def display_coaching_summary(
    session: CoachingSession,
) -> None:
    """Display the coaching-session summary."""
    print("\nFinancial Health")
    print("----------------------------------------")
    print(f"Score:                 " f"{session.financial_health_score:.0f}/100")
    print(f"Status:                " f"{session.financial_health_status}")
    print(f"Generated:             " f"{_format_generated_at(session)}")

    print("\nSummary")
    print("----------------------------------------")
    print(session.summary)


def display_top_advice(
    session: CoachingSession,
) -> None:
    """Display the highest-priority coaching recommendation."""
    print("\nTop Recommendation")
    print("----------------------------------------")

    top_advice = session.top_advice

    if top_advice is None:
        print("No optimizer recommendation is available.")
        return

    print(top_advice.title)
    print(f"Priority:              " f"{top_advice.priority.value}")
    print(f"Category:              " f"{top_advice.category.value}")

    if top_advice.score is not None:
        print(f"Scenario Score:        " f"{top_advice.score:.2f}/100")

    print(f"\n{top_advice.message}")
    print(f"\nRecommended Action: " f"{top_advice.action}")

    if top_advice.expected_impact:
        print(f"\nExpected Impact: " f"{top_advice.expected_impact}")

    explanation = session.get_explanation(top_advice.key)

    if explanation is None:
        return

    print("\nWhy This Matters")
    print("----------------------------------------")
    print(explanation.why_it_matters)

    if explanation.projected_effects:
        print("\nProjected Effects")

        for effect in explanation.projected_effects:
            print(f"- {effect}")

    if explanation.assumptions:
        print("\nAssumptions")

        for assumption in explanation.assumptions:
            print(f"- {assumption}")


def display_coaching_insights(
    session: CoachingSession,
) -> None:
    """Display prioritized financial coaching insights."""
    print("\nKey Financial Insights")
    print("----------------------------------------")

    if not session.insights:
        print("No additional financial insights " "are available.")
        return

    symbols = {
        InsightSeverity.POSITIVE: "+",
        InsightSeverity.INFORMATIONAL: "i",
        InsightSeverity.WARNING: "!",
        InsightSeverity.CRITICAL: "!!",
    }

    for insight in session.insights:
        symbol = symbols[insight.severity]

        print(f"{symbol} {insight.title} " f"[{insight.severity.value}]")
        print(f"  {insight.message}")

        if insight.action:
            print(f"  Action: {insight.action}")


def display_next_steps(
    session: CoachingSession,
) -> None:
    """Display prioritized coaching next steps."""
    print("\nRecommended Next Steps")
    print("----------------------------------------")

    if not session.next_steps:
        print("No immediate next steps were generated.")
        return

    for index, step in enumerate(
        session.next_steps,
        start=1,
    ):
        print(f"{index}. {step}")


def display_coaching_warnings(
    session: CoachingSession,
) -> None:
    """Display important coaching warnings."""
    print("\nImportant Considerations")
    print("----------------------------------------")

    if not session.warnings:
        print("No significant warnings were identified.")
        return

    for warning in session.warnings:
        print(f"- {warning}")


def display_complete_coaching_session(
    session: CoachingSession,
) -> None:
    """Display a complete financial coaching session."""
    print("\n========================================")
    print("          AI Financial Coach")
    print("========================================")

    display_coaching_summary(session)
    display_top_advice(session)
    display_coaching_insights(session)
    display_next_steps(session)
    display_coaching_warnings(session)

    print("========================================")
