"""Lazily-constructed, process-wide Anthropic client."""

import anthropic

from src.core import config

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Return a lazily-constructed, process-wide Anthropic client."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client
