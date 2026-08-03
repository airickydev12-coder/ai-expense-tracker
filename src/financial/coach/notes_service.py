from datetime import datetime, timezone
from pathlib import Path

from src.core.config import DB_PATH
from src.core.logging import get_logger
from src.financial.coach.notes_repository import (
    load_notes_from_file,
    save_notes_to_file,
)

logger = get_logger(__name__)

_notes: list[dict] = []
_loaded_file_path: Path = DB_PATH


def load_notes(
    file_path: Path = DB_PATH,
) -> None:
    """Load saved notes into application memory."""
    global _loaded_file_path

    _notes.clear()
    _notes.extend(load_notes_from_file(file_path))

    _loaded_file_path = file_path


def save_notes(
    file_path: Path | None = None,
) -> None:
    """Save all saved notes."""
    target_path = file_path if file_path is not None else _loaded_file_path

    save_notes_to_file(_notes, target_path)


def get_notes() -> list[dict]:
    """Return a copy of all saved notes."""
    return _notes.copy()


def _get_next_note_id() -> int:
    """Return the next available note ID."""
    if not _notes:
        return 1

    return max(note["id"] for note in _notes) + 1


def add_note(
    title: str,
    content: str,
    file_path: Path | None = None,
    *,
    now: datetime | None = None,
) -> dict:
    """Create and persist a new saved note."""
    note = {
        "id": _get_next_note_id(),
        "created_at": (now if now is not None else datetime.now(timezone.utc)).isoformat(),
        "title": title.strip(),
        "content": content.strip(),
    }

    _notes.append(note)
    save_notes(file_path)

    logger.info(
        "Saved note %d (%s)",
        note["id"],
        note["title"],
    )

    return note


def delete_note(
    note_id: int,
    file_path: Path | None = None,
) -> dict | None:
    """Delete a saved note by ID."""
    for index, note in enumerate(_notes):
        if note["id"] == note_id:
            deleted_note = _notes.pop(index)
            save_notes(file_path)
            logger.info(
                "Deleted note %d",
                note_id,
            )
            return deleted_note

    return None


def clear_notes() -> None:
    """Clear saved notes from application memory."""
    _notes.clear()
