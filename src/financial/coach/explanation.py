from src.financial.coach.models import (
    AdviceExplanation,
    CoachingAdvice,
)
from src.financial.scenarios.models import (
    ScenarioResult,
)
from src.financial.scenarios.report import (
    build_scenario_comparison_report,
)


def _format_change(
    metric: str,
    change: float,
) -> str:
    """Format one projected financial change."""
    if metric == "Health Score":
        return f"{metric} changes by " f"{change:+.2f} points."

    return f"{metric} changes by " f"{change:+,.2f}."


def explain_coaching_advice(
    advice: CoachingAdvice,
    scenario_result: ScenarioResult,
) -> AdviceExplanation:
    """Explain coaching advice using scenario evidence."""
    report = build_scenario_comparison_report(scenario_result)

    projected_effects = [
        _format_change(
            comparison.metric,
            comparison.change,
        )
        for comparison in report.comparisons
        if abs(comparison.change) > 0.005
    ]

    assumptions = [
        (f"{assumption.name}: " f"{assumption.value}")
        for assumption in (scenario_result.assumptions)
    ]

    risks = [
        *scenario_result.risks,
        *advice.warnings,
    ]

    summary = (
        f"{advice.title} is recommended as a "
        f"{advice.priority.value.lower()}-priority action."
    )

    why_it_matters = f"{advice.reason} " f"{advice.expected_impact}"

    return AdviceExplanation(
        advice_key=advice.key,
        summary=summary,
        why_it_matters=why_it_matters,
        projected_effects=projected_effects,
        assumptions=assumptions,
        risks=risks,
    )


def build_plain_language_explanation(
    advice: CoachingAdvice,
) -> str:
    """Build a concise explanation without scenario details."""
    lines = [
        advice.message,
        "",
        f"Why this matters: {advice.reason}",
        "",
        f"Recommended action: {advice.action}",
    ]

    if advice.expected_impact:
        lines.extend(
            [
                "",
                ("Expected impact: " f"{advice.expected_impact}"),
            ]
        )

    if advice.warnings:
        lines.extend(
            [
                "",
                "Important considerations:",
            ]
        )

        lines.extend(f"- {warning}" for warning in advice.warnings)

    return "\n".join(lines)
