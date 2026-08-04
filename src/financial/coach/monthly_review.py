"""AI-generated monthly financial review, grounded in stored snapshot history."""

import json
from datetime import datetime
from decimal import Decimal

import anthropic

from src.core import ai_client
from src.core.exceptions import ExternalServiceError
from src.core.logging import get_logger
from src.financial.application.recommendation_application_service import (
    build_recommendations,
)
from src.financial.history.analytics import (
    filter_history_within_days,
    get_category_totals_change,
)
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.service import get_history
from src.financial.history.trend_summary import FinancialTrendSummary
from src.financial.history.trends import CURRENCY_TREND_THRESHOLD, analyze_financial_trends
from src.financial.recommendations.models import Recommendation

logger = get_logger(__name__)

REVIEW_WINDOW_DAYS = 31
CATEGORY_TREND_LIMIT = 3

_CATEGORY_TREND_GAP_NOTE = (
    "Category-level spending trends aren't available in this review because "
    "per-category totals aren't currently persisted in snapshot history."
)

_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_summary": {"type": "string"},
        "income_expenses_narrative": {"type": "string"},
        "cash_flow_narrative": {"type": "string"},
        "debt_narrative": {"type": "string"},
        "savings_narrative": {"type": "string"},
        "goals_narrative": {"type": "string"},
        "health_score_narrative": {"type": "string"},
        "next_actions_narrative": {"type": "string"},
    },
    "required": [
        "overall_summary",
        "income_expenses_narrative",
        "cash_flow_narrative",
        "debt_narrative",
        "savings_narrative",
        "goals_narrative",
        "health_score_narrative",
        "next_actions_narrative",
    ],
    "additionalProperties": False,
}


def _format_goal_line(goal: dict) -> str:
    """Format one goal's current progress for the prompt."""
    target = goal["target_amount"]
    current = goal["current_amount"]
    percent = float(current / target * 100) if target > 0 else 0.0
    return (
        f"- {goal['name']}: {percent:.0f}% complete "
        f"(${current:,.2f} of ${target:,.2f})"
    )


def _build_category_trends(category_changes: dict[str, Decimal]) -> list[dict]:
    """Filter, sort, and cap category-level spending changes for display."""
    notable = [
        (category, change)
        for category, change in category_changes.items()
        if abs(change) >= CURRENCY_TREND_THRESHOLD
    ]
    notable.sort(key=lambda item: abs(item[1]), reverse=True)

    return [
        {
            "category": category,
            "change": change,
            "direction": "Increasing" if change > 0 else "Decreasing",
        }
        for category, change in notable[:CATEGORY_TREND_LIMIT]
    ]


def _build_prompt(
    current_snapshot: dict,
    trend: FinancialTrendSummary,
    top_actions: list[Recommendation],
    window_days: int,
    category_trends: list[dict],
) -> str:
    """Build the monthly-review prompt from real, precomputed data."""
    goal_lines = (
        "\n".join(
            _format_goal_line(goal) for goal in current_snapshot.get("goals", [])
        )
        or "No goals are currently tracked."
    )

    action_lines = (
        "\n".join(f"- {action.title}: {action.action}" for action in top_actions)
        or "No active recommendations."
    )

    category_trend_lines = (
        "\n".join(
            f"- {item['category']}: {item['direction']} by ${abs(item['change']):,.2f}"
            for item in category_trends
        )
        or "No notable category-level spending shifts this period."
    )

    return (
        "Write a monthly financial review covering the last "
        f"{window_days} days, grounded only in the real numbers given "
        "below -- do not invent numbers. Respond with: overall_summary "
        "(2-3 sentences); income_expenses_narrative (income vs. expenses "
        "this period, mentioning any notable category-level spending "
        "shifts listed below if there are any); cash_flow_narrative; "
        "debt_narrative; savings_narrative; goals_narrative (current "
        "progress, using the goal list below); health_score_narrative "
        "(referencing the change over the period, not just the current "
        "score); and next_actions_narrative (introducing the top actions "
        "below, without inventing new ones). Each field should be 1-3 "
        "sentences of plain prose, no markdown.\n\n"
        f"Current health score: {current_snapshot['health_score']}/100 "
        f"({current_snapshot['health_status']})\n"
        f"Health score change over period: {trend.health_score.change} "
        f"({trend.health_score.direction.value})\n"
        f"Net worth change over period: ${trend.net_worth.change:,.2f} "
        f"({trend.net_worth.direction.value})\n"
        f"Cash flow change over period: ${trend.cash_flow.change:,.2f} "
        f"({trend.cash_flow.direction.value})\n"
        f"Income change over period: ${trend.income.change:,.2f} "
        f"({trend.income.direction.value})\n"
        f"Expense change over period: ${trend.expenses.change:,.2f} "
        f"({trend.expenses.direction.value})\n"
        f"Overall momentum: {trend.overall_momentum.value}\n"
        f"Current total debt: ${current_snapshot['total_debt']:,.2f}\n"
        f"Current net worth: ${current_snapshot['net_worth']:,.2f}\n"
        f"Notable category-level spending shifts this period:\n{category_trend_lines}\n"
        f"Goals:\n{goal_lines}\n"
        f"Top recommended actions:\n{action_lines}"
    )


def _request_review(prompt: str) -> dict:
    """Call Claude to generate structured monthly-review narrative fields.

    Kept thin and separately monkeypatchable so tests never make a live
    network call.
    """
    client = ai_client.get_client()
    try:
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=1536,
            output_config={
                "format": {"type": "json_schema", "schema": _REVIEW_SCHEMA},
                "effort": "medium",
            },
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as exc:
        logger.warning("Anthropic monthly review generation failed: %s", exc)
        raise ExternalServiceError(f"Monthly review is unavailable: {exc}") from exc

    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        raise ExternalServiceError("Monthly review returned no usable response.")
    return json.loads(text)


def _build_no_history_review(current_snapshot: dict) -> dict:
    """Build a degraded review when no snapshot has ever been recorded."""
    return {
        "status": "no_history",
        "message": (
            "No financial snapshot has been recorded yet. Record one via "
            "POST /history/snapshot (or the CLI's 'Record Snapshot Now' "
            "option) to enable monthly reviews."
        ),
    }


def _build_insufficient_recent_history_review(
    windowed_count: int,
    latest: FinancialSnapshotRecord,
) -> dict:
    """Build a degraded review when there isn't enough recent history."""
    return {
        "status": "insufficient_recent_history",
        "message": (
            f"Only {windowed_count} snapshot(s) were recorded in the last "
            f"{REVIEW_WINDOW_DAYS} days (at least 2 are needed for a "
            "monthly review). The most recent snapshot was recorded on "
            f"{latest.timestamp.date().isoformat()}."
        ),
        "last_recorded_snapshot": latest.timestamp.isoformat(),
    }


def _build_ok_review(
    current_snapshot: dict,
    trend: FinancialTrendSummary,
    top_actions: list[Recommendation],
    windowed: list[FinancialSnapshotRecord],
) -> dict:
    """Build the full review, calling the LLM for narrative sections only."""
    category_changes = get_category_totals_change(windowed)
    category_trends = _build_category_trends(category_changes)

    review = _request_review(
        _build_prompt(
            current_snapshot, trend, top_actions, REVIEW_WINDOW_DAYS, category_trends
        )
    )

    known_gaps = [] if category_changes else [_CATEGORY_TREND_GAP_NOTE]

    return {
        "status": "ok",
        "period_start": windowed[0].timestamp.isoformat(),
        "period_end": windowed[-1].timestamp.isoformat(),
        "overall_summary": review["overall_summary"],
        "income_vs_expenses": {
            "narrative": review["income_expenses_narrative"],
            "income_change": trend.income.change,
            "expense_change": trend.expenses.change,
        },
        "cash_flow": {
            "narrative": review["cash_flow_narrative"],
            "change": trend.cash_flow.change,
            "direction": trend.cash_flow.direction.value,
        },
        "debt_progress": {
            "narrative": review["debt_narrative"],
            "total_debt": current_snapshot["total_debt"],
        },
        "savings_progress": {
            "narrative": review["savings_narrative"],
        },
        "goal_status": {
            "narrative": review["goals_narrative"],
        },
        "health_score": {
            "narrative": review["health_score_narrative"],
            "change": trend.health_score.change,
            "direction": trend.health_score.direction.value,
            "current_score": current_snapshot["health_score"],
        },
        "top_actions": [
            {
                "key": action.key,
                "title": action.title,
                "message": action.message,
                "action": action.action,
                "priority": action.priority.name,
            }
            for action in top_actions
        ],
        "category_trends": category_trends,
        "known_gaps": known_gaps,
    }


def generate_monthly_review(
    user_id: int,
    current_snapshot: dict,
    *,
    now: datetime | None = None,
) -> dict:
    """Generate a structured monthly financial review, grounded in real history."""
    logger.info("Requesting monthly review generation for user %d", user_id)

    history = get_history(user_id)
    if not history:
        return _build_no_history_review(current_snapshot)

    windowed = filter_history_within_days(history, REVIEW_WINDOW_DAYS, now=now)
    if len(windowed) < 2:
        latest = max(history, key=lambda record: record.timestamp)
        return _build_insufficient_recent_history_review(len(windowed), latest)

    trend = analyze_financial_trends(windowed)
    top_actions = build_recommendations(user_id, limit=3)

    return _build_ok_review(current_snapshot, trend, top_actions, windowed)
