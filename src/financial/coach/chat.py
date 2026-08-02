"""AI financial coach chat via a manual Claude tool-use loop."""

import json
from datetime import date
from typing import Any, Callable, cast

import anthropic

from src.core import ai_client
from src.core.exceptions import ExternalServiceError
from src.core.logging import get_logger
from src.financial.accounts.service import get_accounts
from src.financial.application.financial_state import build_current_financial_snapshot
from src.financial.bills.analytics import (
    get_bills_due_soon,
    get_total_unpaid_bill_amount,
    get_unpaid_bills,
)
from src.financial.bills.service import get_bills
from src.financial.budgets.analytics import get_budget_summary
from src.financial.budgets.service import get_budgets
from src.financial.application.recommendation_application_service import (
    build_recommendations,
)
from src.financial.coach.coaching import build_coaching_session
from src.financial.coach.recommendation_explainer import get_recommendation_evidence
from src.financial.coach.saved_content import search_saved_content
from src.financial.debt.analytics import (
    get_highest_interest_debt,
    get_total_debt,
    get_total_minimum_payments,
)
from src.financial.debt.service import get_debts
from src.financial.expenses.analytics import (
    get_average,
    get_category_totals,
    get_highest_expense,
    get_lowest_expense,
    get_total,
)
from src.financial.expenses.service import get_expenses
from src.financial.goals.analytics import get_goal_progress_percentage, get_total_goal_progress
from src.financial.goals.service import get_goals
from src.financial.income.analytics import get_average_income, get_total_income
from src.financial.income.service import get_income_entries
from src.financial.scenarios.models import ScenarioRequest, ScenarioType
from src.financial.scenarios.optimizer import optimize_financial_snapshot
from src.financial.scenarios.service import run_financial_scenario

logger = get_logger(__name__)

MAX_TOOL_USE_ITERATIONS = 5

_SYSTEM_PROMPT = (
    "You are a personal financial coach embedded in this app. You answer "
    "questions about the user's own finances using the tools provided — "
    "every tool reads real data from the user's account, runs a real "
    "calculation, or simulates a real scenario. Never guess a number or "
    "invent an outcome; call a tool to get it. If no tool covers what's "
    "being asked, say so rather than inventing data.\n\n"
    "You are strictly read-only over the user's stored data: you cannot "
    "create, modify, or delete any expense, budget, debt, goal, bill, "
    "income entry, or account. Running a scenario is different — it is a "
    "pure, non-persisted calculation, not a data mutation, so you CAN and "
    "should run one whenever the user asks a \"what if\" question (e.g. "
    "\"what if I cut dining out by 20%\" or \"what if I paid an extra $100 "
    "toward my credit card\"), using the run_scenario tool. For a debt "
    "scenario, call get_debt_details first to find the real debt_id before "
    "calling run_scenario — never guess an id. After running a scenario, "
    "present the real calculated result to the user and compare it against "
    "their current numbers rather than restating the raw tool output "
    "verbatim.\n\n"
    "When asked what to prioritize or which recommendations matter most, "
    "call list_recommendations rather than inventing a priority order. "
    "When asked why a specific recommendation matters or what impact acting "
    "on it would have, call recommendation_evidence and cite the real "
    "numbers it returns — never fabricate a dollar amount, a timeline, or a "
    "percentage.\n\n"
    "When asked about past decisions, prior monthly reviews, or previously "
    "saved scenarios (e.g. \"what did we decide about my emergency fund "
    "last month\"), call search_saved_content and answer from what it "
    "actually returns. If nothing relevant is found, say so honestly "
    "rather than inventing a past conversation or decision.\n\n"
    "Be warm but direct, like a knowledgeable friend, not a salesperson. "
    "Keep answers focused and concise — lead with the answer, then the "
    "supporting numbers. Avoid disclaimers about not being a licensed "
    "financial advisor unless the user asks something that genuinely "
    "requires one."
)

# --- tool implementations (all zero-argument, all JSON-serializable) -------


def _tool_financial_snapshot() -> dict:
    return build_current_financial_snapshot()


def _tool_expense_details() -> dict:
    expenses = get_expenses()
    highest = get_highest_expense(expenses)
    lowest = get_lowest_expense(expenses)
    return {
        "expenses": [expense.to_dict() for expense in expenses],
        "total": get_total(expenses),
        "average": get_average(expenses),
        "category_totals": get_category_totals(expenses),
        "highest_expense": highest.to_dict() if highest else None,
        "lowest_expense": lowest.to_dict() if lowest else None,
    }


def _tool_budget_status() -> dict:
    budgets = get_budgets()
    expenses = get_expenses()
    return {
        "budgets": [
            {**budget.to_dict(), "summary": get_budget_summary(budget, expenses)}
            for budget in budgets
        ]
    }


def _tool_debt_details() -> dict:
    debts = get_debts()
    highest = get_highest_interest_debt(debts)
    return {
        "debts": [debt.to_dict() for debt in debts],
        "total_debt": get_total_debt(debts),
        "total_minimum_payments": get_total_minimum_payments(debts),
        "highest_interest_debt": highest.to_dict() if highest else None,
    }


def _tool_goal_details() -> dict:
    goals = get_goals()
    return {
        "goals": [
            {**goal.to_dict(), "progress_percentage": get_goal_progress_percentage(goal)}
            for goal in goals
        ],
        "total_goal_progress": get_total_goal_progress(goals),
    }


def _tool_bill_details() -> dict:
    bills = get_bills()
    current_day = date.today().day
    return {
        "bills": [bill.to_dict() for bill in bills],
        "unpaid_bills": [bill.to_dict() for bill in get_unpaid_bills(bills)],
        "bills_due_soon": [bill.to_dict() for bill in get_bills_due_soon(bills, current_day)],
        "total_unpaid_amount": get_total_unpaid_bill_amount(bills),
    }


def _tool_income_details() -> dict:
    income_entries = get_income_entries()
    return {
        "income_entries": [income.to_dict() for income in income_entries],
        "total_income": get_total_income(income_entries),
        "average_income": get_average_income(income_entries),
    }


def _tool_account_details() -> dict:
    return {"accounts": [account.to_dict() for account in get_accounts()]}


def _tool_coach_analysis() -> dict:
    snapshot = build_current_financial_snapshot()
    optimization_result = optimize_financial_snapshot(snapshot, register_handlers=False)
    session = build_coaching_session(snapshot, optimization_result)
    return session.to_dict()


# --- tool implementations that take parameters -----------------------------

_SCENARIO_PARAM_KEYS: dict[ScenarioType, tuple[str, ...]] = {
    ScenarioType.EXPENSE_REDUCTION: ("category", "reduction_percentage", "horizon_months"),
    ScenarioType.INCOME_INCREASE: ("increase_percentage", "horizon_months"),
    ScenarioType.EXTRA_DEBT_PAYMENT: ("debt_id", "extra_monthly_payment", "horizon_months"),
    ScenarioType.ADDITIONAL_SAVINGS: ("additional_monthly_savings", "horizon_months"),
}


def _tool_run_scenario(
    scenario_type: str,
    name: str,
    description: str = "",
    category: str | None = None,
    reduction_percentage: float | None = None,
    increase_percentage: float | None = None,
    debt_id: int | None = None,
    extra_monthly_payment: float | None = None,
    additional_monthly_savings: float | None = None,
    horizon_months: int | None = None,
) -> dict:
    """Simulate a real financial scenario and return the calculated result."""
    scenario_type_enum = ScenarioType(scenario_type)

    all_fields = {
        "category": category,
        "reduction_percentage": reduction_percentage,
        "increase_percentage": increase_percentage,
        "debt_id": debt_id,
        "extra_monthly_payment": extra_monthly_payment,
        "additional_monthly_savings": additional_monthly_savings,
        "horizon_months": horizon_months,
    }

    relevant_keys = _SCENARIO_PARAM_KEYS[scenario_type_enum]
    parameters = {
        key: all_fields[key] for key in relevant_keys if all_fields[key] is not None
    }

    snapshot = build_current_financial_snapshot()

    request = ScenarioRequest(
        scenario_type=scenario_type_enum,
        name=name,
        description=description,
        parameters=parameters,
    )

    result = run_financial_scenario(request, snapshot)

    return result.to_dict()


def _tool_list_recommendations(
    category: str | None = None,
    priority: str | None = None,
    limit: int | None = None,
) -> dict:
    recommendations = build_recommendations(
        priority=priority,
        category=category,
        limit=limit if limit is not None else 5,
    )
    return {"recommendations": [recommendation.to_dict() for recommendation in recommendations]}


def _tool_recommendation_evidence(recommendation_key: str) -> dict:
    return get_recommendation_evidence(recommendation_key)


def _tool_search_saved_content(
    query: str | None = None,
    limit: int | None = None,
) -> dict:
    return search_saved_content(query, limit if limit is not None else 5)


_TOOL_FUNCTIONS: dict[str, Callable[..., dict]] = {
    "get_financial_snapshot": _tool_financial_snapshot,
    "get_expense_details": _tool_expense_details,
    "get_budget_status": _tool_budget_status,
    "get_debt_details": _tool_debt_details,
    "get_goal_details": _tool_goal_details,
    "get_bill_details": _tool_bill_details,
    "get_income_details": _tool_income_details,
    "get_account_details": _tool_account_details,
    "get_coach_analysis": _tool_coach_analysis,
    "run_scenario": _tool_run_scenario,
    "list_recommendations": _tool_list_recommendations,
    "recommendation_evidence": _tool_recommendation_evidence,
    "search_saved_content": _tool_search_saved_content,
}

_EMPTY_SCHEMA = {"type": "object", "properties": {}, "additionalProperties": False}

_RUN_SCENARIO_SCHEMA = {
    "type": "object",
    "properties": {
        "scenario_type": {
            "type": "string",
            "enum": [scenario_type.value for scenario_type in ScenarioType],
            "description": "Which kind of financial scenario to simulate.",
        },
        "name": {
            "type": "string",
            "description": "A short name for this scenario.",
        },
        "description": {
            "type": "string",
            "description": "A one-sentence description of what this scenario models.",
        },
        "category": {
            "type": "string",
            "description": "Expense category name -- required for Expense Reduction.",
        },
        "reduction_percentage": {
            "type": "number",
            "description": (
                "Percent to reduce spending by, 0-100 -- required for "
                "Expense Reduction."
            ),
        },
        "increase_percentage": {
            "type": "number",
            "description": "Percent to increase income by -- required for Income Increase.",
        },
        "debt_id": {
            "type": "integer",
            "description": (
                "The real debt ID from get_debt_details -- required for "
                "Extra Debt Payment. Never guess this value."
            ),
        },
        "extra_monthly_payment": {
            "type": "number",
            "description": (
                "Additional monthly payment amount -- required for Extra "
                "Debt Payment."
            ),
        },
        "additional_monthly_savings": {
            "type": "number",
            "description": (
                "Additional monthly savings amount -- required for "
                "Additional Savings."
            ),
        },
        "horizon_months": {
            "type": "integer",
            "description": "Projection horizon in months. Defaults to 12 if omitted.",
        },
    },
    "required": ["scenario_type", "name"],
    "additionalProperties": False,
}

_LIST_RECOMMENDATIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "description": (
                "Filter to one category, e.g. 'Debt', 'Savings', 'Cash Flow'. "
                "Omit for all categories."
            ),
        },
        "priority": {
            "type": "string",
            "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "description": "Filter to one priority level. Omit for all.",
        },
        "limit": {
            "type": "integer",
            "description": "Maximum number of recommendations to return. Defaults to 5.",
        },
    },
    "required": [],
    "additionalProperties": False,
}

_RECOMMENDATION_EVIDENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "recommendation_key": {
            "type": "string",
            "description": (
                "The key of a debt-category recommendation, from "
                "list_recommendations or get_coach_analysis."
            ),
        },
    },
    "required": ["recommendation_key"],
    "additionalProperties": False,
}

_SEARCH_SAVED_CONTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": (
                "A keyword or phrase to search for, e.g. 'emergency fund'. "
                "Omit to return the most recent saved items instead."
            ),
        },
        "limit": {
            "type": "integer",
            "description": "Maximum number of matches to return per source. Defaults to 5.",
        },
    },
    "required": [],
    "additionalProperties": False,
}

_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_financial_snapshot",
        "description": (
            "Call this first for almost any question. Returns the full current "
            "financial picture in one call: total income, total expenses, net "
            "cash flow, total account balance, total debt, net worth, goal "
            "progress, financial health score/status, and spending by category."
        ),
        "input_schema": _EMPTY_SCHEMA,
    },
    {
        "name": "get_expense_details",
        "description": (
            "Call this when asked about individual expenses, spending by "
            "category, or the highest/lowest/average expense."
        ),
        "input_schema": _EMPTY_SCHEMA,
    },
    {
        "name": "get_budget_status",
        "description": (
            "Call this when asked whether spending is on/under/over budget, "
            "or about a specific budget's limit and remaining amount."
        ),
        "input_schema": _EMPTY_SCHEMA,
    },
    {
        "name": "get_debt_details",
        "description": (
            "Call this when asked about debts, balances, interest rates, or "
            "minimum payments."
        ),
        "input_schema": _EMPTY_SCHEMA,
    },
    {
        "name": "get_goal_details",
        "description": "Call this when asked about savings goals and their progress.",
        "input_schema": _EMPTY_SCHEMA,
    },
    {
        "name": "get_bill_details",
        "description": (
            "Call this when asked about bills, which bills are unpaid, or "
            "what's due soon."
        ),
        "input_schema": _EMPTY_SCHEMA,
    },
    {
        "name": "get_income_details",
        "description": "Call this when asked about income sources or total/average income.",
        "input_schema": _EMPTY_SCHEMA,
    },
    {
        "name": "get_account_details",
        "description": "Call this when asked about account balances.",
        "input_schema": _EMPTY_SCHEMA,
    },
    {
        "name": "get_coach_analysis",
        "description": (
            "Call this when asked for overall advice, next steps, or "
            "'how am I doing' — returns the app's own deterministic coaching "
            "analysis (health score, prioritized advice, insights, warnings, "
            "next steps) so you can ground broad advice in it rather than "
            "inventing your own."
        ),
        "input_schema": _EMPTY_SCHEMA,
    },
    {
        "name": "run_scenario",
        "description": (
            "Call this to simulate a hypothetical financial change (a 'what "
            "if' question) — reducing a spending category, increasing "
            "income, paying extra toward a debt, or saving more each month. "
            "Returns the real calculated result, including the projected "
            "impact compared to the current baseline. This is a pure "
            "calculation, not a data mutation — nothing is saved. For a "
            "debt scenario, call get_debt_details first to find the real "
            "debt_id; never guess it."
        ),
        "input_schema": _RUN_SCENARIO_SCHEMA,
    },
    {
        "name": "list_recommendations",
        "description": (
            "Call this when asked what to prioritize, which recommendations "
            "matter most, or for a ranked list of action items. Returns "
            "recommendations already sorted by priority, optionally filtered "
            "by category or priority level."
        ),
        "input_schema": _LIST_RECOMMENDATIONS_SCHEMA,
    },
    {
        "name": "recommendation_evidence",
        "description": (
            "Call this when asked why a specific debt-related recommendation "
            "matters or what impact acting on it would have. Returns real, "
            "precomputed evidence (the recommendation plus supporting "
            "numbers, e.g. a debt's balance/rate and a real payoff "
            "projection) for you to cite directly — never invent these "
            "numbers yourself."
        ),
        "input_schema": _RECOMMENDATION_EVIDENCE_SCHEMA,
    },
    {
        "name": "search_saved_content",
        "description": (
            "Call this when asked about past decisions, prior monthly "
            "reviews, or previously saved 'what if' scenarios — e.g. 'what "
            "did we decide about my emergency fund last month' or 'what "
            "scenarios have I saved'. Searches saved monthly reviews and "
            "saved scenarios by keyword, most recent first. If nothing "
            "relevant comes back, say so honestly rather than inventing a "
            "past decision."
        ),
        "input_schema": _SEARCH_SAVED_CONTENT_SCHEMA,
    },
]


def _execute_tool(name: str, tool_input: dict) -> tuple[str, bool]:
    """Run one tool call, returning (content, is_error) for a tool_result block."""
    func = _TOOL_FUNCTIONS.get(name)
    if func is None:
        return f"Unknown tool: {name!r}", True
    try:
        result = func(**tool_input)
    except Exception as exc:  # noqa: BLE001 - tool-dispatch boundary, must never crash the loop
        logger.warning("Coach chat tool %r failed: %s", name, exc)
        return str(exc), True
    return json.dumps(result, default=str), False


def _request_completion(messages: list[dict]) -> anthropic.types.Message:
    """Call Claude with the tool set.

    Kept thin and separately monkeypatchable so tests never make a live
    network call.
    """
    client = ai_client.get_client()
    try:
        return client.messages.create(
            model="claude-opus-5",
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            tools=cast(list[anthropic.types.ToolUnionParam], _TOOL_DEFINITIONS),
            output_config={"effort": "medium"},
            messages=cast(list[anthropic.types.MessageParam], messages),
        )
    except anthropic.APIError as exc:
        logger.warning("Anthropic coach chat failed: %s", exc)
        raise ExternalServiceError(f"Coach chat is unavailable: {exc}") from exc


def run_coach_chat(history: list[dict[str, str]]) -> str:
    """Run the tool-use loop for one turn and return the assistant's reply text.

    `history` is the full conversation so far, including the newest user
    message, as [{"role": "user"|"assistant", "content": str}, ...].
    """
    logger.info("Running coach chat with %d prior message(s)", len(history))
    messages: list[dict] = [{"role": m["role"], "content": m["content"]} for m in history]

    for _ in range(MAX_TOOL_USE_ITERATIONS):
        response = _request_completion(messages)

        if response.stop_reason != "tool_use":
            text = next((block.text for block in response.content if block.type == "text"), None)
            if text is None:
                raise ExternalServiceError("Coach chat returned no usable response.")
            return text

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            content, is_error = _execute_tool(block.name, block.input)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": content,
                    "is_error": is_error,
                }
            )
        messages.append({"role": "user", "content": tool_results})

    raise ExternalServiceError(
        "Coach chat could not produce a response within the tool-use budget."
    )
