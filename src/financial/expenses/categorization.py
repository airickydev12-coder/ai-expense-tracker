"""AI-assisted expense category suggestion via the Claude API."""

import json

import anthropic

from src.core import ai_client
from src.core.exceptions import ExternalServiceError
from src.core.logging import get_logger
from src.financial.shared.categories import ExpenseCategory

logger = get_logger(__name__)

_CATEGORY_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": [c.value for c in ExpenseCategory]},
    },
    "required": ["category"],
    "additionalProperties": False,
}


def _request_category(name: str) -> str:
    """Call Claude to suggest a category string for an expense name.

    Kept thin and separately monkeypatchable so tests never make a live
    network call.
    """
    client = ai_client.get_client()
    try:
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=256,
            output_config={
                "format": {"type": "json_schema", "schema": _CATEGORY_SCHEMA},
                "effort": "low",
            },
            messages=[
                {
                    "role": "user",
                    "content": (
                        f'Suggest the single best expense category for an '
                        f'expense named "{name}".'
                    ),
                }
            ],
        )
    except anthropic.APIError as exc:
        logger.warning("Anthropic category suggestion failed: %s", exc)
        raise ExternalServiceError(
            f"Category suggestion is unavailable: {exc}"
        ) from exc

    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        raise ExternalServiceError("Category suggestion returned no usable response.")
    return json.loads(text)["category"]


def suggest_category(name: str) -> ExpenseCategory:
    """Suggest an ExpenseCategory for the given expense name via Claude."""
    logger.info("Requesting category suggestion for expense name=%r", name)
    return ExpenseCategory(_request_category(name))
