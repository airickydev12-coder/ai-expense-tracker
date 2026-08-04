"""Pragmatic personal-RAG retrieval over saved monthly reviews, scenarios, and notes.

Keyword/recency retrieval, not vector/semantic search -- deliberately, for a
single-user app whose saved-content corpus is small (see Phase 7 Stage 3
plan). Structured financial data (balances, transactions, goals, bills,
recommendations) is never retrieved this way; it stays in its own domain
services and tables.
"""

import json

from src.financial.coach.monthly_review_history_service import (
    get_monthly_review_history,
)
from src.financial.coach.notes_service import get_notes
from src.financial.scenarios.workspace_service import get_scenario_workspace


def _matches(record_json: str, query: str) -> bool:
    """Case-insensitive substring match against a JSON-serialized record."""
    return query.strip().lower() in record_json.lower()


def search_monthly_reviews(
    user_id: int,
    query: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Return a user's saved monthly reviews, most recent first, optionally keyword-filtered."""
    reviews = sorted(
        get_monthly_review_history(user_id),
        key=lambda review: review["generated_at"],
        reverse=True,
    )

    if query:
        reviews = [
            review
            for review in reviews
            if _matches(json.dumps(review, default=str), query)
        ]

    return reviews[:limit]


def search_saved_scenarios(
    user_id: int,
    query: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Return a user's saved scenario_workspace results, optionally keyword-filtered."""
    results = get_scenario_workspace(user_id).get_results()

    if query:
        results = [
            result
            for result in results
            if _matches(json.dumps(result.to_dict(), default=str), query)
        ]

    return [result.to_dict() for result in results[:limit]]


def search_saved_notes(
    user_id: int,
    query: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Return a user's saved notes, most recent first, optionally keyword-filtered."""
    notes = sorted(
        get_notes(user_id),
        key=lambda note: note["created_at"],
        reverse=True,
    )

    if query:
        notes = [note for note in notes if _matches(json.dumps(note, default=str), query)]

    return notes[:limit]


def search_saved_content(
    user_id: int,
    query: str | None = None,
    limit: int = 5,
) -> dict:
    """Search a user's saved monthly reviews, saved scenarios, and saved notes together."""
    return {
        "monthly_reviews": search_monthly_reviews(user_id, query, limit),
        "scenarios": search_saved_scenarios(user_id, query, limit),
        "notes": search_saved_notes(user_id, query, limit),
    }
