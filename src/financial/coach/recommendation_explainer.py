"""AI-generated structured explanation for a single DEBT-category recommendation."""

import json
from decimal import Decimal

import anthropic

from src.core import ai_client
from src.core.exceptions import (
    BusinessRuleError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from src.core.logging import get_logger
from src.financial.application.financial_state import build_current_financial_snapshot
from src.financial.application.recommendation_application_service import (
    get_recommendation_by_key,
)
from src.financial.coach.insights import calculate_debt_to_income_ratio
from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.scenarios.debt_scenario import calculate_debt_payoff
from src.financial.scenarios.optimizer import DEFAULT_EXTRA_DEBT_PAYMENTS

logger = get_logger(__name__)

_EXPLANATION_SCHEMA = {
    "type": "object",
    "properties": {
        "reason": {"type": "string"},
        "expected_impact": {"type": "string"},
        "confidence": {"type": "string", "enum": ["Low", "Medium", "High"]},
        "assumptions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["reason", "expected_impact", "confidence", "assumptions"],
    "additionalProperties": False,
}


def _select_high_interest_debt(debts: list[dict]) -> dict | None:
    """Mirror HighInterestDebtRule's selection: first balance>0 & rate>=15."""
    for debt in debts:
        if debt["balance"] > 0 and debt["interest_rate"] >= 15:
            return debt
    return None


def _select_highest_interest_debt(debts: list[dict]) -> dict | None:
    """Mirror DebtPayoffPriorityRule's selection: max active debt by rate."""
    active_debts = [debt for debt in debts if debt["balance"] > 0]
    if not active_debts:
        return None

    highest = max(active_debts, key=lambda debt: debt["interest_rate"])
    if highest["interest_rate"] <= 0:
        return None

    return highest


def _select_missing_minimum_payment_debt(debts: list[dict]) -> dict | None:
    """Mirror DebtMinimumPaymentRule's selection: first balance>0 & no minimum."""
    for debt in debts:
        if debt["balance"] > 0 and debt["minimum_payment"] <= 0:
            return debt
    return None


_DEBT_RULE_SELECTORS = {
    "HighInterestDebtRule": _select_high_interest_debt,
    "DebtPayoffPriorityRule": _select_highest_interest_debt,
    "DebtMinimumPaymentRule": _select_missing_minimum_payment_debt,
}


def _resolve_target_debt(
    recommendation: Recommendation,
    snapshot: dict,
) -> dict | None:
    """
    Resolve which single debt a recommendation refers to, if any.

    Returns None for aggregate-level rules (DebtToIncomeRule, DebtRatioRule)
    or when the mirrored selection doesn't match the recommendation's own
    message -- callers should fall back to aggregate evidence in that case
    rather than risk presenting the wrong debt.
    """
    selector = _DEBT_RULE_SELECTORS.get(recommendation.source_rule)
    if selector is None:
        return None

    debt = selector(snapshot.get("debts", []))
    if debt is None:
        return None

    if debt["name"].lower() not in recommendation.message.lower():
        logger.warning(
            "Resolved debt %r did not match recommendation message for "
            "source_rule=%r; falling back to aggregate evidence.",
            debt["name"],
            recommendation.source_rule,
        )
        return None

    return debt


def _choose_extra_payment(net_cash_flow: Decimal) -> float:
    """Pick the largest default candidate payment that fits current cash flow."""
    affordable = [
        amount for amount in DEFAULT_EXTRA_DEBT_PAYMENTS if amount <= net_cash_flow
    ]
    if affordable:
        return max(affordable)
    return min(DEFAULT_EXTRA_DEBT_PAYMENTS)


def _build_debt_evidence(debt: dict, snapshot: dict) -> dict:
    """Build real, precomputed debt-specific evidence -- never LLM-authored."""
    extra_payment = _choose_extra_payment(snapshot["net_cash_flow"])
    interest_rate = Decimal(str(debt["interest_rate"]))

    evidence: dict = {
        "type": "debt",
        "debt_name": debt["name"],
        "debt_balance": debt["balance"],
        "interest_rate": debt["interest_rate"],
        "minimum_payment": debt["minimum_payment"],
        "extra_monthly_payment": extra_payment,
        "payoff_months_saved": None,
        "total_interest_saved": None,
        "total_debt": snapshot["total_debt"],
    }

    try:
        baseline = calculate_debt_payoff(
            balance=debt["balance"],
            annual_interest_rate=interest_rate,
            monthly_payment=debt["minimum_payment"],
            horizon_months=12,
        )
        accelerated = calculate_debt_payoff(
            balance=debt["balance"],
            annual_interest_rate=interest_rate,
            monthly_payment=debt["minimum_payment"] + Decimal(str(extra_payment)),
            horizon_months=12,
        )
    except (ValidationError, BusinessRuleError) as exc:
        logger.warning("Could not project debt payoff for explanation: %s", exc)
        return evidence

    evidence["payoff_months_saved"] = max(
        baseline.payoff_months - accelerated.payoff_months,
        0,
    )
    evidence["total_interest_saved"] = max(
        baseline.total_interest - accelerated.total_interest,
        Decimal("0"),
    )

    return evidence


def _build_aggregate_evidence(snapshot: dict) -> dict:
    """Build real, precomputed aggregate debt evidence for non-single-debt rules."""
    return {
        "type": "aggregate",
        "total_debt": snapshot["total_debt"],
        "total_income": snapshot["total_income"],
        "debt_to_income_ratio": calculate_debt_to_income_ratio(snapshot),
        "total_account_balance": snapshot["total_account_balance"],
        "total_goal_progress": snapshot["total_goal_progress"],
    }


def _build_prompt(recommendation: Recommendation, evidence: dict) -> str:
    """Build the recommendation-explanation prompt from real evidence."""
    evidence_lines = "\n".join(f"{key}: {value}" for key, value in evidence.items())

    return (
        "You are explaining one financial recommendation to a user. Given the "
        "recommendation and the real evidence below, respond with a reason "
        "(why this matters), an expected_impact (phrase using the real numbers "
        "given -- do not invent numbers not present in the evidence), a "
        "confidence level (Low, Medium, or High), and a short list of "
        "assumptions underlying the projection (e.g. income and other required "
        "expenses remain stable). Do not restate the recommendation title/action "
        "verbatim; explain the reasoning behind it.\n\n"
        f"Recommendation title: {recommendation.title}\n"
        f"Recommendation message: {recommendation.message}\n"
        f"Recommendation action: {recommendation.action}\n"
        f"Priority: {recommendation.priority.name}\n\n"
        f"Evidence:\n{evidence_lines}"
    )


def _request_explanation(prompt: str) -> dict:
    """Call Claude to generate structured recommendation-explanation fields.

    Kept thin and separately monkeypatchable so tests never make a live
    network call.
    """
    client = ai_client.get_client()
    try:
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=768,
            output_config={
                "format": {"type": "json_schema", "schema": _EXPLANATION_SCHEMA},
                "effort": "medium",
            },
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as exc:
        logger.warning("Anthropic recommendation explanation failed: %s", exc)
        raise ExternalServiceError(
            f"Recommendation explanation is unavailable: {exc}"
        ) from exc

    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        raise ExternalServiceError(
            "Recommendation explanation returned no usable response."
        )
    return json.loads(text)


def explain_debt_recommendation(recommendation_key: str) -> dict:
    """Generate a structured, evidence-grounded explanation for a DEBT recommendation."""
    recommendation = get_recommendation_by_key(recommendation_key)
    if recommendation is None:
        raise NotFoundError(
            f"No recommendation was found with key: {recommendation_key}"
        )

    if recommendation.category != RecommendationCategory.DEBT:
        raise ValidationError(
            "Recommendation explanations are currently only available "
            "for debt-category recommendations."
        )

    logger.info(
        "Requesting explanation for recommendation key=%r",
        recommendation_key,
    )

    snapshot = build_current_financial_snapshot()

    debt = _resolve_target_debt(recommendation, snapshot)
    evidence = (
        _build_debt_evidence(debt, snapshot)
        if debt is not None
        else _build_aggregate_evidence(snapshot)
    )

    prompt = _build_prompt(recommendation, evidence)
    explanation = _request_explanation(prompt)

    return {
        "recommendation_key": recommendation.key,
        "reason": explanation["reason"],
        "evidence": evidence,
        "expected_impact": explanation["expected_impact"],
        "confidence": explanation["confidence"],
        "assumptions": explanation["assumptions"],
    }
