"""AI financial coach API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.schemas.coach import (
    CoachChatRequest,
    CoachChatResponse,
    CoachNarrativeResponse,
    MonthlyReviewResponse,
    RecommendationExplanationResponse,
    SaveNoteRequest,
    SavedNoteResponse,
)
from src.core.exceptions import ValidationError
from src.financial.application.financial_state import (
    build_current_financial_snapshot,
)
from src.financial.coach import chat as coach_chat
from src.financial.coach import monthly_review as coach_monthly_review
from src.financial.coach import narrative as coach_narrative
from src.financial.coach import recommendation_explainer
from src.financial.coach.coaching import build_coaching_session
from src.financial.coach.monthly_review_export import export_monthly_review_to_csv
from src.financial.coach.monthly_review_history_service import record_monthly_review
from src.financial.coach.insights import generate_financial_coach_insights
from src.financial.coach.notes_service import add_note, delete_note, get_notes
from src.financial.scenarios.optimizer import optimize_financial_snapshot

router = APIRouter(prefix="/coach", tags=["Coach"])


@router.get("/narrative")
def get_financial_narrative() -> CoachNarrativeResponse:
    """Return an AI-generated narrative explanation of the current snapshot."""
    snapshot = build_current_financial_snapshot()
    narrative = coach_narrative.generate_financial_narrative(snapshot)
    return CoachNarrativeResponse(narrative=narrative)


@router.get("/recommendations/{recommendation_key}/explanation")
def get_recommendation_explanation(
    recommendation_key: str,
) -> RecommendationExplanationResponse:
    """Return an AI-generated, evidence-grounded explanation for a recommendation."""
    result = recommendation_explainer.explain_recommendation(recommendation_key)
    return RecommendationExplanationResponse.model_validate(result)


@router.get("/monthly-review")
def get_monthly_review() -> MonthlyReviewResponse:
    """Return an AI-generated monthly financial review."""
    snapshot = build_current_financial_snapshot()
    result = coach_monthly_review.generate_monthly_review(snapshot)
    return MonthlyReviewResponse.model_validate(result)


@router.post("/monthly-review")
def create_monthly_review() -> MonthlyReviewResponse:
    """Generate a monthly review and save it if there's enough data to ground one."""
    snapshot = build_current_financial_snapshot()
    result = coach_monthly_review.generate_monthly_review(snapshot)
    if result["status"] == "ok":
        result = record_monthly_review(result)
    return MonthlyReviewResponse.model_validate(result)


@router.get("/monthly-review/export")
def export_monthly_review() -> StreamingResponse:
    """Return the current monthly review as a downloadable CSV file."""
    snapshot = build_current_financial_snapshot()
    review = coach_monthly_review.generate_monthly_review(snapshot)
    csv_text = export_monthly_review_to_csv(review)
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=monthly_review.csv"},
    )


@router.get("/insights")
def get_insights() -> list[dict[str, Any]]:
    """Return deterministic coaching insights for the current financial state."""
    snapshot = build_current_financial_snapshot()
    insights = generate_financial_coach_insights(snapshot)
    return [insight.to_dict() for insight in insights]


@router.get("/session")
def get_coaching_session() -> dict[str, Any]:
    """Build a complete coaching session from the current financial state."""
    snapshot = build_current_financial_snapshot()
    optimization_result = optimize_financial_snapshot(
        snapshot,
        register_handlers=False,
    )
    session = build_coaching_session(snapshot, optimization_result)
    return session.to_dict()


@router.post("/chat")
def send_chat_message(request: CoachChatRequest) -> CoachChatResponse:
    """Send a message, with full history, to the AI financial coach chat."""
    if request.messages[-1].role != "user":
        raise ValidationError("The last message in the conversation must be from the user.")
    history = [{"role": message.role, "content": message.content} for message in request.messages]
    reply = coach_chat.run_coach_chat(history)
    return CoachChatResponse(reply=reply)


@router.get("/notes")
def list_notes() -> list[SavedNoteResponse]:
    """Return all saved notes, newest first."""
    notes = sorted(get_notes(), key=lambda note: note["created_at"], reverse=True)
    return [SavedNoteResponse.model_validate(note) for note in notes]


@router.post("/notes", status_code=status.HTTP_201_CREATED)
def create_note(request: SaveNoteRequest) -> SavedNoteResponse:
    """Save a new note."""
    note = add_note(title=request.title, content=request.content)
    return SavedNoteResponse.model_validate(note)


@router.delete("/notes/{note_id}")
def remove_note(note_id: int) -> SavedNoteResponse:
    """Delete and return a saved note by ID."""
    deleted = delete_note(note_id)
    if deleted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} was not found.",
        )
    return SavedNoteResponse.model_validate(deleted)
