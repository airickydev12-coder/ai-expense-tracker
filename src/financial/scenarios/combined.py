from copy import deepcopy

from src.financial.scenarios.models import (
    ScenarioRequest,
)
from src.financial.scenarios.plan import (
    ScenarioPlanResult,
    ScenarioPlanStep,
    build_cumulative_scenario_report,
)
from src.financial.scenarios.service import (
    ScenarioService,
    scenario_service,
)


def _extend_unique(
    target: list[str],
    values: list[str],
) -> None:
    """Append unique nonblank strings to a collection."""
    existing = {value.strip().lower() for value in target}

    for value in values:
        normalized = value.strip()

        if not normalized:
            continue

        comparison_key = normalized.lower()

        if comparison_key in existing:
            continue

        existing.add(comparison_key)
        target.append(normalized)


def _get_assumption_value(
    step: ScenarioPlanStep,
    assumption_name: str,
) -> float:
    """Return a numeric assumption value from a plan step."""
    normalized_name = assumption_name.strip().lower()

    for assumption in step.result.assumptions:
        if assumption.name.strip().lower() != normalized_name:
            continue

        try:
            return float(assumption.value)
        except (TypeError, ValueError):
            return 0.0

    return 0.0


def detect_plan_conflicts(
    original_snapshot: dict,
    projected_snapshot: dict,
    steps: list[ScenarioPlanStep],
) -> list[str]:
    """Detect conflicts created by combined scenario commitments."""
    conflicts: list[str] = []

    original_cash_flow = float(
        original_snapshot.get(
            "net_cash_flow",
            0.0,
        )
    )

    projected_cash_flow = float(
        projected_snapshot.get(
            "net_cash_flow",
            0.0,
        )
    )

    additional_savings = sum(
        _get_assumption_value(
            step,
            "Additional Monthly Savings",
        )
        for step in steps
    )

    extra_debt_payments = sum(
        _get_assumption_value(
            step,
            "Extra Monthly Payment",
        )
        for step in steps
    )

    total_new_commitments = additional_savings + extra_debt_payments

    if total_new_commitments > original_cash_flow:
        conflicts.append(
            "Combined additional savings and debt-payment "
            "commitments exceed the original monthly net cash flow."
        )

    if projected_cash_flow < 0:
        conflicts.append(
            "The combined scenario plan produces negative " "monthly net cash flow."
        )

    for step in steps:
        for risk in step.result.risks:
            normalized_risk = risk.lower()

            if (
                "exceeds current monthly net cash flow" in normalized_risk
                or "negative monthly available cash flow" in normalized_risk
            ):
                _extend_unique(
                    conflicts,
                    [f"{step.result.name}: " f"{risk}"],
                )

    return conflicts


def run_combined_scenario_plan(
    *,
    name: str,
    description: str,
    requests: list[ScenarioRequest],
    snapshot: dict,
    service: ScenarioService | None = None,
) -> ScenarioPlanResult:
    """Apply multiple scenarios sequentially to one snapshot."""
    normalized_name = name.strip()

    if not normalized_name:
        raise ValueError("Combined scenario plan name cannot be empty.")

    if not requests:
        raise ValueError("At least one scenario request is required.")

    active_service = service if service is not None else scenario_service

    original_snapshot = deepcopy(snapshot)
    evolving_snapshot = deepcopy(snapshot)

    steps: list[ScenarioPlanStep] = []
    benefits: list[str] = []
    risks: list[str] = []
    recommendations: list[str] = []

    for order, request in enumerate(
        requests,
        start=1,
    ):
        result = active_service.run(
            request=request,
            snapshot=evolving_snapshot,
        )

        step = ScenarioPlanStep(
            order=order,
            request=request,
            result=result,
        )

        steps.append(step)

        evolving_snapshot = deepcopy(result.projected_snapshot)

        _extend_unique(
            benefits,
            result.benefits,
        )
        _extend_unique(
            risks,
            result.risks,
        )
        _extend_unique(
            recommendations,
            result.recommendations,
        )

    cumulative_report = build_cumulative_scenario_report(
        original_snapshot,
        evolving_snapshot,
    )

    conflicts = detect_plan_conflicts(
        original_snapshot,
        evolving_snapshot,
        steps,
    )

    if conflicts:
        _extend_unique(
            risks,
            conflicts,
        )

        _extend_unique(
            recommendations,
            [
                (
                    "Reduce or reprioritize monthly commitments "
                    "until the combined plan maintains positive "
                    "available cash flow."
                )
            ],
        )

    return ScenarioPlanResult(
        name=normalized_name,
        description=description,
        original_snapshot=original_snapshot,
        projected_snapshot=evolving_snapshot,
        steps=steps,
        cumulative_report=cumulative_report,
        conflicts=conflicts,
        benefits=benefits,
        risks=risks,
        recommendations=recommendations,
    )
