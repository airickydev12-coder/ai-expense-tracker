"""AI-generated structured explanation for a financial recommendation."""

import json
from decimal import Decimal
from typing import Callable

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
from src.financial.recommendations.models import Recommendation
from src.financial.rules.bill_due_rule import (
    BILL_DUE_WINDOW_MAX_DAYS,
    BILL_DUE_WINDOW_MIN_DAYS,
)
from src.financial.rules.budget_rule import BUDGET_UTILIZATION_CRITICAL_THRESHOLD
from src.financial.rules.expense_spike_rule import EXPENSE_SPIKE_MULTIPLIER
from src.financial.scenarios.debt_scenario import calculate_debt_payoff
from src.financial.scenarios.optimizer import DEFAULT_EXTRA_DEBT_PAYMENTS
from src.financial.shared.thresholds import SPENDING_CONCENTRATION_THRESHOLD

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

# --- entity selectors: each mirrors its source rule's own selection logic --


def _select_high_interest_debt(snapshot: dict) -> dict | None:
    """Mirror HighInterestDebtRule's selection: first balance>0 & rate>=15."""
    for debt in snapshot.get("debts", []):
        if debt["balance"] > 0 and debt["interest_rate"] >= 15:
            return debt
    return None


def _select_highest_interest_debt(snapshot: dict) -> dict | None:
    """Mirror DebtPayoffPriorityRule's selection: max active debt by rate."""
    active_debts = [debt for debt in snapshot.get("debts", []) if debt["balance"] > 0]
    if not active_debts:
        return None

    highest = max(active_debts, key=lambda debt: debt["interest_rate"])
    if highest["interest_rate"] <= 0:
        return None

    return highest


def _select_missing_minimum_payment_debt(snapshot: dict) -> dict | None:
    """Mirror DebtMinimumPaymentRule's selection: first balance>0 & no minimum."""
    for debt in snapshot.get("debts", []):
        if debt["balance"] > 0 and debt["minimum_payment"] <= 0:
            return debt
    return None


def _select_completed_goal(snapshot: dict) -> dict | None:
    """Mirror GoalCompletionRule's selection: first fully-funded goal."""
    for goal in snapshot.get("goals", []):
        if goal["target_amount"] > 0 and goal["current_amount"] >= goal["target_amount"]:
            return goal
    return None


def _select_low_progress_goal(snapshot: dict) -> dict | None:
    """Mirror GoalProgressThresholdRule's selection: first goal <25% funded."""
    for goal in snapshot.get("goals", []):
        target_amount = goal["target_amount"]
        if target_amount <= 0:
            continue
        if goal["current_amount"] / target_amount < 0.25:
            return goal
    return None


def _select_bill_due_soon(snapshot: dict) -> dict | None:
    """Mirror BillDueSoonRule's selection: first unpaid bill due within the window."""
    current_day = snapshot.get("current_day")
    if current_day is None:
        return None

    for bill in snapshot.get("bills", []):
        if bill["is_paid"]:
            continue

        days_until_due = bill["due_day"] - current_day
        if BILL_DUE_WINDOW_MIN_DAYS <= days_until_due <= BILL_DUE_WINDOW_MAX_DAYS:
            return bill

    return None


def _select_overrun_budget(snapshot: dict) -> dict | None:
    """Mirror BudgetOverrunRule's selection: first budget over its limit."""
    for budget in snapshot.get("budget_report", []):
        if budget["remaining"] < 0:
            return budget
    return None


def _select_high_utilization_budget(snapshot: dict) -> dict | None:
    """Mirror BudgetUtilizationRule's selection: first nearly-exhausted budget."""
    for budget in snapshot.get("budget_report", []):
        limit = budget["limit"]
        if limit <= 0:
            continue
        if budget["spent"] / limit >= BUDGET_UTILIZATION_CRITICAL_THRESHOLD:
            return budget
    return None


def _select_expense_spike(snapshot: dict) -> dict | None:
    """Mirror ExpenseSpikeRule's selection: the largest expense, if it spikes."""
    largest_expense = snapshot.get("largest_expense")
    average_expense = snapshot.get("average_expense")

    if largest_expense is None or average_expense is None or average_expense <= 0:
        return None

    if largest_expense["amount"] < average_expense * EXPENSE_SPIKE_MULTIPLIER:
        return None

    return largest_expense


def _select_concentrated_category(snapshot: dict) -> dict | None:
    """Mirror SpendingConcentrationRule's selection: the dominant spending category."""
    category_totals = snapshot.get("category_totals", {})
    if not category_totals:
        return None

    total_spending = sum(category_totals.values())
    if total_spending <= 0:
        return None

    largest_category = max(category_totals, key=category_totals.get)
    largest_amount = category_totals[largest_category]

    if largest_amount / total_spending < SPENDING_CONCENTRATION_THRESHOLD:
        return None

    return {"category": largest_category, "amount": largest_amount}


def _choose_extra_payment(net_cash_flow: Decimal) -> float:
    """Pick the largest default candidate payment that fits current cash flow."""
    affordable = [
        amount for amount in DEFAULT_EXTRA_DEBT_PAYMENTS if amount <= net_cash_flow
    ]
    if affordable:
        return max(affordable)
    return min(DEFAULT_EXTRA_DEBT_PAYMENTS)


# --- evidence builders: real, precomputed fields -- never LLM-authored -----


def _build_debt_evidence(debt: dict, snapshot: dict) -> dict:
    """Build real, precomputed debt-specific evidence, including payoff projection."""
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


def _build_goal_evidence(goal: dict, snapshot: dict) -> dict:
    """Build real, precomputed goal-specific evidence."""
    target_amount = goal["target_amount"]
    current_amount = goal["current_amount"]

    return {
        "type": "goal",
        "goal_name": goal["name"],
        "target_amount": target_amount,
        "current_amount": current_amount,
        "progress_percentage": (
            float(current_amount / target_amount * 100) if target_amount > 0 else 0.0
        ),
    }


def _build_bill_evidence(bill: dict, snapshot: dict) -> dict:
    """Build real, precomputed bill-specific evidence."""
    current_day = snapshot.get("current_day")

    return {
        "type": "bill",
        "bill_name": bill["name"],
        "amount": bill["amount"],
        "due_day": bill["due_day"],
        "days_until_due": (
            bill["due_day"] - current_day if current_day is not None else None
        ),
        "is_paid": bill["is_paid"],
    }


def _build_budget_evidence(budget: dict, snapshot: dict) -> dict:
    """Build real, precomputed budget-specific evidence."""
    limit = budget["limit"]
    spent = budget["spent"]

    return {
        "type": "budget",
        "category": budget["category"],
        "limit": limit,
        "spent": spent,
        "remaining": budget["remaining"],
        "utilization_percentage": (
            float(spent / limit * 100) if limit > 0 else 0.0
        ),
    }


def _build_expense_evidence(expense: dict, snapshot: dict) -> dict:
    """Build real, precomputed expense-spike evidence."""
    return {
        "type": "expense",
        "expense_name": expense["name"],
        "expense_category": expense["category"],
        "amount": expense["amount"],
        "average_expense": snapshot.get("average_expense"),
    }


def _build_expense_category_evidence(entity: dict, snapshot: dict) -> dict:
    """Build real, precomputed spending-concentration evidence."""
    category_totals = snapshot.get("category_totals", {})
    total_spending = sum(category_totals.values()) if category_totals else Decimal("0")
    amount = entity["amount"]

    return {
        "type": "expense_category_concentration",
        "category": entity["category"],
        "amount": amount,
        "total_spending": total_spending,
        "concentration_percentage": (
            float(amount / total_spending * 100) if total_spending > 0 else 0.0
        ),
    }


def _build_aggregate_evidence(snapshot: dict) -> dict:
    """Build real, precomputed aggregate evidence for non-entity-specific rules."""
    return {
        "type": "aggregate",
        "total_income": snapshot["total_income"],
        "total_expenses": snapshot["total_expenses"],
        "net_cash_flow": snapshot["net_cash_flow"],
        "total_account_balance": snapshot["total_account_balance"],
        "total_goal_progress": snapshot["total_goal_progress"],
        "total_debt": snapshot["total_debt"],
        "net_worth": snapshot["net_worth"],
        "health_score": snapshot["health_score"],
        "health_status": snapshot["health_status"],
        "debt_to_income_ratio": calculate_debt_to_income_ratio(snapshot),
    }


# --- registry-driven dispatch -----------------------------------------------

_ENTITY_RULES: dict[str, tuple[Callable[[dict], dict | None], str, Callable[[dict, dict], dict]]] = {
    "HighInterestDebtRule": (_select_high_interest_debt, "name", _build_debt_evidence),
    "DebtPayoffPriorityRule": (_select_highest_interest_debt, "name", _build_debt_evidence),
    "DebtMinimumPaymentRule": (
        _select_missing_minimum_payment_debt,
        "name",
        _build_debt_evidence,
    ),
    "GoalCompletionRule": (_select_completed_goal, "name", _build_goal_evidence),
    "GoalProgressThresholdRule": (_select_low_progress_goal, "name", _build_goal_evidence),
    "BillDueSoonRule": (_select_bill_due_soon, "name", _build_bill_evidence),
    "BudgetOverrunRule": (_select_overrun_budget, "category", _build_budget_evidence),
    "BudgetUtilizationRule": (
        _select_high_utilization_budget,
        "category",
        _build_budget_evidence,
    ),
    "ExpenseSpikeRule": (_select_expense_spike, "name", _build_expense_evidence),
    "SpendingConcentrationRule": (
        _select_concentrated_category,
        "category",
        _build_expense_category_evidence,
    ),
}


def _gather_evidence(recommendation: Recommendation, snapshot: dict) -> dict:
    """
    Resolve the target entity (if any) and build real, precomputed evidence.

    Falls back to aggregate evidence for rules with no single-entity
    selector, when the selector finds nothing, or when the resolved
    entity's identifying name/category doesn't appear in the
    recommendation's own message -- never risk presenting the wrong entity.
    """
    entry = _ENTITY_RULES.get(recommendation.source_rule)
    if entry is None:
        return _build_aggregate_evidence(snapshot)

    selector, message_key, evidence_builder = entry
    entity = selector(snapshot)
    if entity is None:
        return _build_aggregate_evidence(snapshot)

    identifier = str(entity[message_key])
    if identifier.lower() not in recommendation.message.lower():
        logger.warning(
            "Resolved entity %r did not match recommendation message for "
            "source_rule=%r; falling back to aggregate evidence.",
            identifier,
            recommendation.source_rule,
        )
        return _build_aggregate_evidence(snapshot)

    return evidence_builder(entity, snapshot)


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


def _get_recommendation(user_id: int, recommendation_key: str) -> Recommendation:
    """Look up a recommendation by key, raising if none exists."""
    recommendation = get_recommendation_by_key(user_id, recommendation_key)
    if recommendation is None:
        raise NotFoundError(
            f"No recommendation was found with key: {recommendation_key}"
        )

    return recommendation


def get_recommendation_evidence(user_id: int, recommendation_key: str) -> dict:
    """
    Return a recommendation plus real, precomputed evidence -- no AI call.

    Shares lookup/evidence-gathering with explain_recommendation(), but
    stops short of generating an AI narrative -- used by the coach chat's
    evidence-lookup tool, which lets the already-running chat model write
    its own grounded explanation instead of triggering a second, nested
    Claude call.
    """
    recommendation = _get_recommendation(user_id, recommendation_key)
    snapshot = build_current_financial_snapshot(user_id)
    evidence = _gather_evidence(recommendation, snapshot)

    return {
        "recommendation": recommendation.to_dict(),
        "evidence": evidence,
    }


def explain_recommendation(user_id: int, recommendation_key: str) -> dict:
    """Generate a structured, evidence-grounded explanation for a recommendation."""
    recommendation = _get_recommendation(user_id, recommendation_key)

    logger.info(
        "Requesting explanation for recommendation key=%r for user %d",
        recommendation_key,
        user_id,
    )

    snapshot = build_current_financial_snapshot(user_id)
    evidence = _gather_evidence(recommendation, snapshot)

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
