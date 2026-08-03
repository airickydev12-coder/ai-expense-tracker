from datetime import datetime, timezone
from pathlib import Path

from src.core.config import DB_PATH
from src.core.logging import get_logger
from src.financial.coach.notes_repository import (
    load_notes_from_file,
    save_notes_to_file,
)

logger = get_logger(__name__)

_notes: dict[int, list[dict]] = {}


def _ensure_loaded(user_id: int, db_path: Path = DB_PATH) -> None:
    """Lazily load a user's saved notes into the cache on first access."""
    if user_id not in _notes:
        _notes[user_id] = load_notes_from_file(user_id, db_path)


def load_notes(user_id: int, db_path: Path = DB_PATH) -> None:
    """Force-reload a user's saved notes from the repository."""
    _notes[user_id] = load_notes_from_file(user_id, db_path)


def save_notes(user_id: int, db_path: Path = DB_PATH) -> None:
    """Save all of this user's saved notes using the repository."""
    save_notes_to_file(_notes[user_id], user_id, db_path)


def get_notes(user_id: int, db_path: Path = DB_PATH) -> list[dict]:
    """Return a copy of all of this user's saved notes."""
    _ensure_loaded(user_id, db_path)
    return _notes[user_id].copy()


def _get_next_note_id(user_id: int) -> int:
    """Return the next available note ID for this user."""
    user_notes = _notes.get(user_id, [])
    if not user_notes:
        return 1

    return max(note["id"] for note in user_notes) + 1


def add_note(
    user_id: int,
    title: str,
    content: str,
    db_path: Path = DB_PATH,
    *,
    now: datetime | None = None,
) -> dict:
    """Create and persist a new saved note for this user."""
    _ensure_loaded(user_id, db_path)

    note = {
        "id": _get_next_note_id(user_id),
        "created_at": (now if now is not None else datetime.now(timezone.utc)).isoformat(),
        "title": title.strip(),
        "content": content.strip(),
    }

    _notes[user_id].append(note)
    save_notes(user_id, db_path)

    logger.info(
        "Saved note %d (%s) for user %d",
        note["id"],
        note["title"],
        user_id,
    )

    return note


def delete_note(
    user_id: int,
    note_id: int,
    db_path: Path = DB_PATH,
) -> dict | None:
    """Delete one of this user's saved notes by ID."""
    _ensure_loaded(user_id, db_path)

    for index, note in enumerate(_notes[user_id]):
        if note["id"] == note_id:
            deleted_note = _notes[user_id].pop(index)
            save_notes(user_id, db_path)
            logger.info(
                "Deleted note %d for user %d",
                note_id,
                user_id,
            )
            return deleted_note

    return None


def clear_notes() -> None:
    """Clear saved notes from application memory."""
    _notes.clear()
