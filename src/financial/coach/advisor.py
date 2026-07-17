from src.financial.coach.models import (
    CoachingAdvice,
    CoachingCategory,
    CoachingPriority,
)
from src.financial.scenarios.optimizer import (
    OptimizationResult,
)
from src.financial.scenarios.ranking import (
    RankedScenario,
)
from src.financial.scenarios.scoring import (
    RiskLevel,
    SustainabilityLevel,
)


def _priority_for_ranked_scenario(
    ranked: RankedScenario,
) -> CoachingPriority:
    """Determine coaching priority for an optimizer result."""
    scenario_score = ranked.scenario_score

    if scenario_score.risk_level == RiskLevel.CRITICAL:
        return CoachingPriority.CRITICAL

    if scenario_score.overall_score >= 85:
        return CoachingPriority.HIGH

    if scenario_score.overall_score >= 70:
        return CoachingPriority.MEDIUM

    return CoachingPriority.LOW


def _category_for_scenario(
    ranked: RankedScenario,
) -> CoachingCategory:
    """Map a scenario type to a coaching category."""
    scenario_type = ranked.result.scenario_type.name

    category_map = {
        "EXPENSE_REDUCTION": (CoachingCategory.SPENDING),
        "INCOME_INCREASE": (CoachingCategory.INCOME),
        "ADDITIONAL_SAVINGS": (CoachingCategory.SAVINGS),
        "EXTRA_DEBT_PAYMENT": (CoachingCategory.DEBT),
    }

    return category_map.get(
        scenario_type,
        CoachingCategory.GENERAL,
    )


def _build_expected_impact(
    ranked: RankedScenario,
) -> str:
    """Describe the strongest projected scenario effects."""
    effects: list[str] = []

    net_worth = ranked.report.get_comparison("Net Worth")

    if net_worth is not None and abs(net_worth.change) > 0.005:
        effects.append("net worth " f"{net_worth.change:+,.2f}")

    cash_flow = ranked.report.get_comparison("Net Cash Flow")

    if cash_flow is not None and abs(cash_flow.change) > 0.005:
        effects.append("monthly cash flow " f"{cash_flow.change:+,.2f}")

    debt = ranked.report.get_comparison("Total Debt")

    if debt is not None and debt.change < -0.005:
        effects.append("debt reduced by " f"{abs(debt.change):,.2f}")

    if not effects:
        return (
            "The scenario produces limited measurable "
            "change in the compared financial metrics."
        )

    return "Projected effects include " + ", ".join(effects) + "."


def build_advice_from_ranked_scenario(
    ranked: RankedScenario,
) -> CoachingAdvice:
    """Convert one ranked scenario into coaching advice."""
    scenario_score = ranked.scenario_score

    action = (
        ranked.result.recommendations[0]
        if ranked.result.recommendations
        else (
            "Review the scenario assumptions and "
            "begin with a manageable implementation step."
        )
    )

    message = (
        f"{ranked.scenario_name} is ranked "
        f"#{ranked.rank} for "
        f"{ranked.ranking_metric.value.lower()}."
    )

    reason = (
        f"{ranked.reason} "
        f"The scenario received an overall score of "
        f"{scenario_score.overall_score:.2f}/100, "
        f"with {scenario_score.risk_level.value.lower()} "
        "risk and "
        f"{scenario_score.sustainability.value.lower()} "
        "sustainability."
    )

    warnings = scenario_score.concerns.copy()

    if scenario_score.sustainability == SustainabilityLevel.POOR:
        warnings.append("The projected plan is not financially sustainable.")

    return CoachingAdvice(
        key=(
            "optimizer:"
            f"{ranked.result.scenario_type.name.lower()}:"
            f"{ranked.scenario_name.lower().replace(' ', '_')}"
        ),
        title=ranked.scenario_name,
        message=message,
        action=action,
        reason=reason,
        priority=_priority_for_ranked_scenario(ranked),
        category=_category_for_scenario(ranked),
        expected_impact=_build_expected_impact(ranked),
        source_scenario=ranked.scenario_name,
        score=scenario_score.overall_score,
        warnings=warnings,
    )


def generate_optimizer_advice(
    optimization_result: OptimizationResult,
    limit: int = 3,
) -> list[CoachingAdvice]:
    """Generate prioritized advice from optimizer rankings."""
    if limit <= 0:
        return []

    advice_items = [
        build_advice_from_ranked_scenario(ranked)
        for ranked in (optimization_result.ranked_scenarios[:limit])
    ]

    priority_order = {
        CoachingPriority.CRITICAL: 0,
        CoachingPriority.HIGH: 1,
        CoachingPriority.MEDIUM: 2,
        CoachingPriority.LOW: 3,
    }

    advice_items.sort(
        key=lambda advice: (
            priority_order[advice.priority],
            -(advice.score or 0),
            advice.title.lower(),
        )
    )

    return advice_items


def get_top_optimizer_advice(
    optimization_result: OptimizationResult,
) -> CoachingAdvice | None:
    """Return the strongest optimizer coaching advice."""
    advice = generate_optimizer_advice(
        optimization_result,
        limit=1,
    )

    if not advice:
        return None

    return advice[0]
