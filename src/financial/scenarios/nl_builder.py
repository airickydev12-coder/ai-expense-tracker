"""AI-assisted natural-language financial scenario parsing via the Claude API."""

import json
from typing import Any

import anthropic

from src.core import ai_client
from src.core.exceptions import ExternalServiceError, ValidationError
from src.core.logging import get_logger
from src.financial.debt.models import Debt
from src.financial.scenarios.models import ScenarioType
from src.financial.shared.categories import ExpenseCategory

logger = get_logger(__name__)

_PARAM_KEYS_BY_TYPE: dict[ScenarioType, set[str]] = {
    ScenarioType.EXPENSE_REDUCTION: {"category", "reduction_percentage", "horizon_months"},
    ScenarioType.INCOME_INCREASE: {"increase_percentage", "horizon_months"},
    ScenarioType.EXTRA_DEBT_PAYMENT: {"debt_id", "extra_monthly_payment", "horizon_months"},
    ScenarioType.ADDITIONAL_SAVINGS: {"additional_monthly_savings", "horizon_months"},
}

_HORIZON_FIELD = {"type": ["integer", "null"]}


def _build_schema(categories: list[str], debt_ids: list[int]) -> dict[str, Any]:
    """Build a per-request JSON schema constraining the scenario draft.

    A discriminated union (one `anyOf` branch per scenario type) instead of a
    flat "all fields optional" schema, so Claude structurally cannot attach an
    irrelevant field (e.g. debt_id on an Expense Reduction draft). category and
    debt_id are further constrained to the live enum of real values so free
    text like "dining out" or "my car loan" resolves to real data.
    """
    debt_id_field: dict[str, Any] = (
        {"type": "integer", "enum": debt_ids} if debt_ids else {"type": "integer"}
    )
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "scenario_type": {"type": "string", "enum": [t.value for t in ScenarioType]},
            "parameters": {
                "anyOf": [
                    {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "enum": categories},
                            "reduction_percentage": {"type": "number"},
                            "horizon_months": _HORIZON_FIELD,
                        },
                        "required": ["category", "reduction_percentage", "horizon_months"],
                        "additionalProperties": False,
                    },
                    {
                        "type": "object",
                        "properties": {
                            "increase_percentage": {"type": "number"},
                            "horizon_months": _HORIZON_FIELD,
                        },
                        "required": ["increase_percentage", "horizon_months"],
                        "additionalProperties": False,
                    },
                    {
                        "type": "object",
                        "properties": {
                            "debt_id": debt_id_field,
                            "extra_monthly_payment": {"type": "number"},
                            "horizon_months": _HORIZON_FIELD,
                        },
                        "required": ["debt_id", "extra_monthly_payment", "horizon_months"],
                        "additionalProperties": False,
                    },
                    {
                        "type": "object",
                        "properties": {
                            "additional_monthly_savings": {"type": "number"},
                            "horizon_months": _HORIZON_FIELD,
                        },
                        "required": ["additional_monthly_savings", "horizon_months"],
                        "additionalProperties": False,
                    },
                ]
            },
        },
        "required": ["name", "description", "scenario_type", "parameters"],
        "additionalProperties": False,
    }


def _build_prompt(text: str, categories: list[str], debts: list[Debt]) -> str:
    """Build the Claude prompt, interpolating live category/debt context."""
    debt_lines = "\n".join(f"- id {d.id}: {d.name}" for d in debts) or "(no debts on file)"
    return (
        "A user typed the following free-text request describing a financial "
        f'"what-if" scenario: "{text}"\n\n'
        "Parse it into a structured scenario draft. Pick the single "
        "best-matching scenario_type. Resolve any category mention (e.g. "
        '"dining out", "eating out") to exactly one of these categories: '
        f"{', '.join(categories)}. Resolve any debt mention (e.g. \"my car "
        f'loan") to the matching debt id from this list:\n{debt_lines}\n\n'
        "Only set horizon_months if the user named a specific time period "
        '(e.g. "over the next 6 months"); otherwise leave it null and the '
        "app will use its own default. Give the scenario a short, "
        "human-readable name and a one-sentence description summarizing "
        "what it does."
    )


def _request_scenario_draft(
    text: str,
    categories: list[str],
    debts: list[Debt],
) -> dict[str, Any]:
    """Call Claude to parse free text into a scenario draft.

    Kept thin and separately monkeypatchable so tests never make a live
    network call.
    """
    client = ai_client.get_client()
    schema = _build_schema(categories, [debt.id for debt in debts])
    try:
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=512,
            output_config={
                "format": {"type": "json_schema", "schema": schema},
                "effort": "low",
            },
            messages=[
                {"role": "user", "content": _build_prompt(text, categories, debts)},
            ],
        )
    except anthropic.APIError as exc:
        logger.warning("Anthropic scenario parsing failed: %s", exc)
        raise ExternalServiceError(f"Scenario parsing is unavailable: {exc}") from exc

    text_block = next((b.text for b in response.content if b.type == "text"), None)
    if text_block is None:
        raise ExternalServiceError("Scenario parsing returned no usable response.")
    return json.loads(text_block)


def parse_scenario_text(
    text: str,
    categories: list[str],
    debts: list[Debt],
) -> dict[str, Any]:
    """Parse free text into a scenario draft shaped like ScenarioRunRequest fields."""
    logger.info("Requesting scenario parse for text=%r", text)
    raw = _request_scenario_draft(text, categories, debts)

    scenario_type = ScenarioType(raw["scenario_type"])
    allowed_keys = _PARAM_KEYS_BY_TYPE[scenario_type]
    parameters = {
        key: value
        for key, value in raw["parameters"].items()
        if key in allowed_keys and value is not None
    }

    if scenario_type == ScenarioType.EXPENSE_REDUCTION:
        parameters["category"] = ExpenseCategory(parameters["category"]).value

    if scenario_type == ScenarioType.EXTRA_DEBT_PAYMENT:
        valid_debt_ids = {debt.id for debt in debts}
        resolved_debt_id = parameters.get("debt_id")
        if valid_debt_ids and resolved_debt_id not in valid_debt_ids:
            raise ValidationError(
                "Could not match a debt for this request (resolved id "
                f"{resolved_debt_id!r} is not on file)."
            )

    return {
        "scenario_type": scenario_type,
        "name": raw["name"],
        "description": raw["description"],
        "parameters": parameters,
    }
