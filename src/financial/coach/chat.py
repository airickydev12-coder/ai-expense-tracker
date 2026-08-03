"""AI financial coach chat via a manual Claude tool-use loop."""

import json
from datetime import date
from typing import Any, Callable, cast

import anthropic

from src.core import ai_client
from src.core.exceptions import ExternalServiceError
from src.core.logging import get_logger
from src.core.money import to_money
from src.financial.accounts.service import get_accounts
from src.financial.application.financial_state import build_current_financial_snapshot
from src.financial.bills.analytics import (
    get_bills_due_soon,
    get_total_unpaid_bill_amount,
    get_unpaid_bills,
)
from src.financial.bills.service import get_bills
from src.financial.budgets.analytics import get_budget_summary
from src.financial.budgets.service import get_budgets, update_budget
from src.financial.application.recommendation_application_service import (
    build_recommendations,
)
from src.financial.coach.coaching import build_coaching_session
from src.financial.coach.notes_service import add_note
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
from src.financial.expenses.service import get_expenses, update_expense
from src.financial.goals.analytics import get_goal_progress_percentage, get_total_goal_progress
from src.financial.goals.service import add_goal, get_goals
from src.financial.income.analytics import get_average_income, get_total_income
from src.financial.income.service import get_income_entries
from src.financial.recommendations.history_service import dismiss_recommendation
from src.financial.scenarios.combined import run_combined_scenario_plan
from src.financial.scenarios.models import ScenarioRequest, ScenarioResult, ScenarioType
from src.financial.scenarios.optimizer import optimize_financial_snapshot
from src.financial.scenarios.service import run_financial_scenario
from src.financial.scenarios.workspace_service import save_result_to_workspace
from src.financial.shared.categories import ExpenseCategory

logger = get_logger(__name__)

MAX_TOOL_USE_ITERATIONS = 5

_SYSTEM_PROMPT = (
    "You are a personal financial coach embedded in this app. You answer "
    "questions about the user's own finances using the tools provided — "
    "every tool reads real data from the user's account, runs a real "
    "calculation, or simulates a real scenario. Never guess a number or "
    "invent an outcome; call a tool to get it. If no tool covers what's "
    "being asked, say so rather than inventing data.\n\n"
    "You cannot delete anything, and you cannot touch debts, bills, income "
    "entries, or accounts at all -- those stay strictly read-only. Running "
    "a scenario is different from a mutation — it is a pure, non-persisted "
    "calculation, so you CAN and should run one whenever the user asks a "
    "\"what if\" question (e.g. \"what if I cut dining out by 20%\" or "
    "\"what if I paid an extra $100 toward my credit card\"), using the "
    "run_scenario tool. For a debt scenario, call get_debt_details first to "
    "find the real debt_id before calling run_scenario — never guess an id. "
    "After running a scenario, present the real calculated result to the "
    "user and compare it against their current numbers rather than "
    "restating the raw tool output verbatim. If the question combines two "
    "or more simultaneous changes (e.g. \"what if I paid extra on my debt "
    "AND saved more each month\"), use build_combined_plan instead of "
    "separate run_scenario calls — it applies the steps cumulatively and "
    "surfaces any real conflicts between the combined commitments (e.g. "
    "they exceed available cash flow together even though each looks fine "
    "alone); always mention any conflicts it returns rather than presenting "
    "the combined numbers as risk-free.\n\n"
    "Exactly six actions are allowed to write, and each requires explicit "
    "approval first: describe the specific action in plain language and "
    "wait for the user's explicit 'yes' or equivalent approval in a later "
    "message before calling the tool with confirmed: true. Never set "
    "confirmed: true unless the user's most recent message clearly approves "
    "that specific action — if it's ambiguous, ask for clarification "
    "instead of guessing. The six actions: dismiss_recommendation (call "
    "list_recommendations first for a real recommendation_key — never "
    "guess one); save_scenario (save a scenario you already ran with "
    "run_scenario); add_goal (create a new savings goal); update_budget "
    "(set a category's monthly limit — creates the budget if none exists "
    "yet); categorize_expense (call get_expense_details first for a real "
    "expense_id — never guess one); and save_note (save a short note the "
    "user wants remembered for later).\n\n"
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


def _build_scenario_request(
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
) -> ScenarioRequest:
    """Build a ScenarioRequest from flat tool arguments."""
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

    return ScenarioRequest(
        scenario_type=scenario_type_enum,
        name=name,
        description=description,
        parameters=parameters,
    )


def _build_and_run_scenario(
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
) -> ScenarioResult:
    """Build a ScenarioRequest from tool arguments and run it for real."""
    request = _build_scenario_request(
        scenario_type,
        name,
        description,
        category,
        reduction_percentage,
        increase_percentage,
        debt_id,
        extra_monthly_payment,
        additional_monthly_savings,
        horizon_months,
    )

    snapshot = build_current_financial_snapshot()

    return run_financial_scenario(request, snapshot)


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
    result = _build_and_run_scenario(
        scenario_type,
        name,
        description,
        category,
        reduction_percentage,
        increase_percentage,
        debt_id,
        extra_monthly_payment,
        additional_monthly_savings,
        horizon_months,
    )
    return result.to_dict()


def _tool_build_combined_plan(
    name: str,
    steps: list[dict],
    description: str = "",
) -> dict:
    """Chain multiple what-if scenarios together and surface any conflicts."""
    requests = [
        _build_scenario_request(
            scenario_type=step["scenario_type"],
            name=step["name"],
            description=step.get("description", ""),
            category=step.get("category"),
            reduction_percentage=step.get("reduction_percentage"),
            increase_percentage=step.get("increase_percentage"),
            debt_id=step.get("debt_id"),
            extra_monthly_payment=step.get("extra_monthly_payment"),
            additional_monthly_savings=step.get("additional_monthly_savings"),
            horizon_months=step.get("horizon_months"),
        )
        for step in steps
    ]

    snapshot = build_current_financial_snapshot()

    plan = run_combined_scenario_plan(
        name=name,
        description=description,
        requests=requests,
        snapshot=snapshot,
    )

    return plan.to_dict()


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


# --- write tools: gated by an explicit confirmed flag ----------------------


def _tool_dismiss_recommendation(
    recommendation_key: str,
    confirmed: bool = False,
    note: str = "",
) -> dict:
    if not confirmed:
        return {
            "dismissed": False,
            "reason": (
                "Not dismissed -- confirmed must be true, and should only "
                "be set once the user has explicitly approved dismissing "
                "this specific recommendation in their most recent message."
            ),
        }
    record = dismiss_recommendation(recommendation_key, note)
    if record is None:
        return {
            "dismissed": False,
            "reason": (
                "That recommendation hasn't been seen yet this session -- "
                "call list_recommendations first to get a valid key."
            ),
        }
    return {
        "dismissed": True,
        "recommendation_key": recommendation_key,
        "status": record.status.value,
    }


def _tool_save_scenario(
    scenario_type: str,
    name: str,
    confirmed: bool = False,
    description: str = "",
    category: str | None = None,
    reduction_percentage: float | None = None,
    increase_percentage: float | None = None,
    debt_id: int | None = None,
    extra_monthly_payment: float | None = None,
    additional_monthly_savings: float | None = None,
    horizon_months: int | None = None,
) -> dict:
    if not confirmed:
        return {
            "saved": False,
            "reason": (
                "Not saved -- confirmed must be true, and should only be "
                "set once the user has explicitly approved saving this "
                "exact scenario in their most recent message."
            ),
        }
    result = _build_and_run_scenario(
        scenario_type,
        name,
        description,
        category,
        reduction_percentage,
        increase_percentage,
        debt_id,
        extra_monthly_payment,
        additional_monthly_savings,
        horizon_months,
    )
    save_result_to_workspace(result)
    return {"saved": True, "name": result.name, "description": result.description}


def _tool_add_goal(
    name: str,
    target_amount: float,
    confirmed: bool = False,
    current_amount: float = 0.0,
) -> dict:
    if not confirmed:
        return {
            "added": False,
            "reason": (
                "Not added -- confirmed must be true, and should only be "
                "set once the user has explicitly approved adding this "
                "exact goal in their most recent message."
            ),
        }
    goal = add_goal(name=name, target_amount=target_amount, current_amount=current_amount)
    return {"added": True, "goal": goal.to_dict()}


def _tool_update_budget(
    category: str,
    limit: float,
    confirmed: bool = False,
) -> dict:
    if not confirmed:
        return {
            "updated": False,
            "reason": (
                "Not updated -- confirmed must be true, and should only be "
                "set once the user has explicitly approved this exact "
                "budget change in their most recent message."
            ),
        }
    budget = update_budget(category=ExpenseCategory(category), limit=to_money(limit))
    return {"updated": True, "budget": budget.to_dict()}


def _tool_categorize_expense(
    expense_id: int,
    category: str,
    confirmed: bool = False,
) -> dict:
    if not confirmed:
        return {
            "categorized": False,
            "reason": (
                "Not categorized -- confirmed must be true, and should only "
                "be set once the user has explicitly approved this exact "
                "recategorization in their most recent message."
            ),
        }
    expense = update_expense(expense_id, category=ExpenseCategory(category))
    if expense is None:
        return {
            "categorized": False,
            "reason": (
                "That expense ID doesn't exist -- call get_expense_details "
                "first to get a real one. Never guess an id."
            ),
        }
    return {"categorized": True, "expense": expense.to_dict()}


def _tool_save_note(
    title: str,
    content: str,
    confirmed: bool = False,
) -> dict:
    if not confirmed:
        return {
            "saved": False,
            "reason": (
                "Not saved -- confirmed must be true, and should only be "
                "set once the user has explicitly approved saving this "
                "exact note in their most recent message."
            ),
        }
    note = add_note(title=title, content=content)
    return {"saved": True, "note": note}


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
    "build_combined_plan": _tool_build_combined_plan,
    "list_recommendations": _tool_list_recommendations,
    "recommendation_evidence": _tool_recommendation_evidence,
    "search_saved_content": _tool_search_saved_content,
    "dismiss_recommendation": _tool_dismiss_recommendation,
    "save_scenario": _tool_save_scenario,
    "add_goal": _tool_add_goal,
    "update_budget": _tool_update_budget,
    "categorize_expense": _tool_categorize_expense,
    "save_note": _tool_save_note,
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

_SCENARIO_STEP_SCHEMA = {
    "type": "object",
    "properties": dict(_RUN_SCENARIO_SCHEMA["properties"]),
    "required": ["scenario_type", "name"],
    "additionalProperties": False,
}

_BUILD_COMBINED_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "A short name for the overall combined plan.",
        },
        "description": {
            "type": "string",
            "description": "A one-sentence description of what this combined plan models.",
        },
        "steps": {
            "type": "array",
            "items": _SCENARIO_STEP_SCHEMA,
            "description": (
                "Two or more scenario steps to apply in sequence, each in "
                "the same shape as run_scenario's parameters. Steps apply "
                "cumulatively -- step 2 sees the effect of step 1."
            ),
        },
    },
    "required": ["name", "steps"],
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
                "The key of any recommendation, from list_recommendations "
                "or get_coach_analysis."
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

_DISMISS_RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "recommendation_key": {
            "type": "string",
            "description": (
                "The key of the recommendation to dismiss, from "
                "list_recommendations. Never guess this value."
            ),
        },
        "confirmed": {
            "type": "boolean",
            "description": (
                "Must be true, and only true once the user has explicitly "
                "approved dismissing this specific recommendation in their "
                "most recent message."
            ),
        },
        "note": {
            "type": "string",
            "description": "Optional short note explaining why it was dismissed.",
        },
    },
    "required": ["recommendation_key", "confirmed"],
    "additionalProperties": False,
}

_SAVE_SCENARIO_SCHEMA = {
    "type": "object",
    "properties": {
        **_RUN_SCENARIO_SCHEMA["properties"],
        "confirmed": {
            "type": "boolean",
            "description": (
                "Must be true, and only true once the user has explicitly "
                "approved saving this exact scenario in their most recent "
                "message."
            ),
        },
    },
    "required": ["scenario_type", "name", "confirmed"],
    "additionalProperties": False,
}

_ADD_GOAL_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "A short name for the goal, e.g. 'Emergency Fund'.",
        },
        "target_amount": {
            "type": "number",
            "description": "The dollar amount the goal is aiming for. Must be greater than 0.",
        },
        "current_amount": {
            "type": "number",
            "description": "Amount already saved toward the goal. Defaults to 0.",
        },
        "confirmed": {
            "type": "boolean",
            "description": (
                "Must be true, and only true once the user has explicitly "
                "approved adding this exact goal in their most recent "
                "message."
            ),
        },
    },
    "required": ["name", "target_amount", "confirmed"],
    "additionalProperties": False,
}

_UPDATE_BUDGET_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": [category.value for category in ExpenseCategory],
            "description": "Which expense category's budget to set.",
        },
        "limit": {
            "type": "number",
            "description": (
                "The new monthly budget limit for this category. If no "
                "budget exists yet for this category, one is created."
            ),
        },
        "confirmed": {
            "type": "boolean",
            "description": (
                "Must be true, and only true once the user has explicitly "
                "approved this exact budget change in their most recent "
                "message."
            ),
        },
    },
    "required": ["category", "limit", "confirmed"],
    "additionalProperties": False,
}

_CATEGORIZE_EXPENSE_SCHEMA = {
    "type": "object",
    "properties": {
        "expense_id": {
            "type": "integer",
            "description": (
                "The real expense ID from get_expense_details. Never guess "
                "this value."
            ),
        },
        "category": {
            "type": "string",
            "enum": [category.value for category in ExpenseCategory],
            "description": "The category to move this expense into.",
        },
        "confirmed": {
            "type": "boolean",
            "description": (
                "Must be true, and only true once the user has explicitly "
                "approved this exact recategorization in their most recent "
                "message."
            ),
        },
    },
    "required": ["expense_id", "category", "confirmed"],
    "additionalProperties": False,
}

_SAVE_NOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "A short title for the note.",
        },
        "content": {
            "type": "string",
            "description": "The note's content -- whatever the user wants remembered.",
        },
        "confirmed": {
            "type": "boolean",
            "description": (
                "Must be true, and only true once the user has explicitly "
                "approved saving this exact note in their most recent "
                "message."
            ),
        },
    },
    "required": ["title", "content", "confirmed"],
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
        "name": "build_combined_plan",
        "description": (
            "Call this instead of separate run_scenario calls when the "
            "user's question combines two or more simultaneous changes "
            "(e.g. \"what if I paid extra on my debt AND saved more each "
            "month\"). Applies each step in sequence — later steps see the "
            "effect of earlier ones — and returns the cumulative result "
            "plus any real conflicts between the combined commitments (e.g. "
            "they exceed available cash flow together even if each looks "
            "fine alone). Always mention any conflicts returned rather than "
            "presenting the combined numbers as risk-free."
        ),
        "input_schema": _BUILD_COMBINED_PLAN_SCHEMA,
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
            "Call this when asked why a specific recommendation matters or "
            "what impact acting on it would have — works for any "
            "recommendation category. Returns real, precomputed evidence "
            "(the recommendation plus supporting numbers specific to what "
            "it's about, e.g. a debt's balance/rate and payoff projection, "
            "a goal's progress, a budget's utilization, a bill's due date, "
            "or overall financial numbers) for you to cite directly — never "
            "invent these numbers yourself."
        ),
        "input_schema": _RECOMMENDATION_EVIDENCE_SCHEMA,
    },
    {
        "name": "search_saved_content",
        "description": (
            "Call this when asked about past decisions, prior monthly "
            "reviews, or previously saved 'what if' scenarios — e.g. 'what "
            "did we decide about my emergency fund last month' or 'what "
            "scenarios have I saved' or 'what notes do I have about X'. "
            "Searches saved monthly reviews, saved scenarios, and saved "
            "notes by keyword, most recent first. If nothing relevant comes "
            "back, say so honestly rather than inventing a past decision."
        ),
        "input_schema": _SEARCH_SAVED_CONTENT_SCHEMA,
    },
    {
        "name": "dismiss_recommendation",
        "description": (
            "Call this to dismiss a specific recommendation, but ONLY after "
            "the user has explicitly approved dismissing it in their most "
            "recent message -- first describe which recommendation you'd "
            "dismiss and wait for their approval. Call list_recommendations "
            "first to get a real recommendation_key; never guess one."
        ),
        "input_schema": _DISMISS_RECOMMENDATION_SCHEMA,
    },
    {
        "name": "save_scenario",
        "description": (
            "Call this to save a scenario you already ran with run_scenario, "
            "but ONLY after the user has explicitly approved saving it in "
            "their most recent message -- first describe the scenario and "
            "wait for their approval. Re-runs the scenario fresh against "
            "current data and stores the result."
        ),
        "input_schema": _SAVE_SCENARIO_SCHEMA,
    },
    {
        "name": "add_goal",
        "description": (
            "Call this to add a new savings goal, but ONLY after the user "
            "has explicitly approved adding it in their most recent message "
            "-- first describe the goal (name and target amount) and wait "
            "for their approval."
        ),
        "input_schema": _ADD_GOAL_SCHEMA,
    },
    {
        "name": "update_budget",
        "description": (
            "Call this to set or change the monthly budget limit for an "
            "expense category, but ONLY after the user has explicitly "
            "approved this exact change in their most recent message -- "
            "first describe the new limit and wait for their approval. "
            "Creates the budget if one doesn't already exist for that "
            "category."
        ),
        "input_schema": _UPDATE_BUDGET_SCHEMA,
    },
    {
        "name": "categorize_expense",
        "description": (
            "Call this to move an expense into a different category, but "
            "ONLY after the user has explicitly approved this exact change "
            "in their most recent message -- first describe which expense "
            "and the new category, and wait for their approval. Call "
            "get_expense_details first to find the real expense_id; never "
            "guess it."
        ),
        "input_schema": _CATEGORIZE_EXPENSE_SCHEMA,
    },
    {
        "name": "save_note",
        "description": (
            "Call this to save a short note the user wants remembered for "
            "later (e.g. 'my landlord raises rent every March'), but ONLY "
            "after the user has explicitly approved saving it in their most "
            "recent message -- first describe what you'd save and wait for "
            "their approval. Saved notes become searchable via "
            "search_saved_content."
        ),
        "input_schema": _SAVE_NOTE_SCHEMA,
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
