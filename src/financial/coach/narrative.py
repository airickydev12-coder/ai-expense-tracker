"""AI-generated narrative explanation of the user's financial snapshot."""

import anthropic

from src.core import ai_client
from src.core.exceptions import ExternalServiceError
from src.core.logging import get_logger
from src.financial.coach.insights import (
    calculate_debt_to_income_ratio,
    calculate_emergency_fund_months,
    calculate_savings_rate,
)
from src.financial.engine.health_score import HealthScoreFactor, explain_health_score

logger = get_logger(__name__)


def _format_metric(value: float | None, suffix: str = "") -> str:
    """Format a derived metric, or explain why it isn't calculable."""
    if value is None:
        return "not calculable"
    return f"{value:.1f}{suffix}"


def _build_goal_progress_summary(goals: list[dict]) -> str:
    """Build a per-goal progress summary line for the prompt."""
    if not goals:
        return "No goals are currently tracked."

    lines = []
    for goal in goals:
        target = goal["target_amount"]
        current = goal["current_amount"]
        percent = float(current / target * 100) if target > 0 else 0.0
        lines.append(
            f"- {goal['name']}: {percent:.0f}% complete "
            f"(${current:,.2f} of ${target:,.2f})"
        )
    return "\n".join(lines)


def _build_budget_summary(budget_report: list[dict]) -> str:
    """Build a per-budget performance summary line for the prompt."""
    if not budget_report:
        return "No budgets are currently tracked."

    lines = [
        f"- {entry['category']}: {entry['status']} "
        f"(spent ${entry['spent']:,.2f} of ${entry['limit']:,.2f} limit)"
        for entry in budget_report
    ]
    return "\n".join(lines)


def _build_health_score_summary(factors: list[HealthScoreFactor]) -> str:
    """Build the health-score factor breakdown for the prompt."""
    return "\n".join(
        f"- {factor.name}: {factor.points:+d} points ({factor.description})"
        for factor in factors
    )


def _build_prompt(
    snapshot: dict,
    savings_rate: float | None,
    debt_to_income: float | None,
    emergency_fund_months: float | None,
    factors: list[HealthScoreFactor],
) -> str:
    """Build the narrative-generation prompt from real, precomputed data."""
    return (
        "Write a 3-5 sentence narrative summarizing the user's current financial "
        'position, in the style of: "Your monthly income is $5,200 and your '
        "recurring expenses are $4,350, leaving approximately $850 in monthly "
        "cash flow. Your largest risk is high-interest credit-card debt, while "
        'your emergency fund currently covers 1.4 months of expenses." Cover '
        "income, spending, cash flow, savings rate, debt, net worth, "
        "emergency-fund coverage, budget performance, and goal progress. Then "
        "explain what is driving the financial health score of "
        f"{snapshot['health_score']}/100 ({snapshot['health_status']}) by "
        "referencing the specific contributing factors listed below -- do not "
        "just restate the number. Only use the numbers given below; if a metric "
        "is marked 'not calculable', say why rather than inventing a value. "
        "Write plain prose only, no headers, no markdown, no bullet points in "
        "your response.\n\n"
        f"Monthly income: ${snapshot['total_income']:,.2f}\n"
        f"Monthly expenses: ${snapshot['total_expenses']:,.2f}\n"
        f"Net cash flow: ${snapshot['net_cash_flow']:,.2f}\n"
        f"Savings rate: {_format_metric(savings_rate, '%')}\n"
        f"Total debt: ${snapshot['total_debt']:,.2f}\n"
        f"Debt-to-income ratio: {_format_metric(debt_to_income, '%')}\n"
        f"Total account balance: ${snapshot['total_account_balance']:,.2f}\n"
        "Emergency fund coverage: "
        f"{_format_metric(emergency_fund_months, ' months')}\n"
        f"Net worth: ${snapshot['net_worth']:,.2f}\n"
        f"Budgets:\n{_build_budget_summary(snapshot.get('budget_report', []))}\n"
        f"Goals:\n{_build_goal_progress_summary(snapshot.get('goals', []))}\n"
        f"Health score breakdown:\n{_build_health_score_summary(factors)}"
    )


def _request_narrative(prompt: str) -> str:
    """Call Claude to generate a financial snapshot narrative.

    Kept thin and separately monkeypatchable so tests never make a live
    network call.
    """
    client = ai_client.get_client()
    try:
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=640,
            output_config={"effort": "medium"},
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as exc:
        logger.warning("Anthropic financial narrative generation failed: %s", exc)
        raise ExternalServiceError(
            f"Financial narrative is unavailable: {exc}"
        ) from exc

    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        raise ExternalServiceError("Financial narrative returned no usable response.")
    return text


def generate_financial_narrative(snapshot: dict) -> str:
    """Generate a narrative explanation of the current financial snapshot."""
    logger.info("Requesting financial narrative generation")

    savings_rate = calculate_savings_rate(snapshot)
    debt_to_income = calculate_debt_to_income_ratio(snapshot)
    emergency_fund_months = calculate_emergency_fund_months(snapshot)
    factors = explain_health_score(snapshot)

    prompt = _build_prompt(
        snapshot,
        savings_rate,
        debt_to_income,
        emergency_fund_months,
        factors,
    )

    return _request_narrative(prompt)
