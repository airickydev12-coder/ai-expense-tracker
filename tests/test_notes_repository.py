import pytest

from src.financial.coach.notes_repository import (
    load_notes_from_file,
    save_notes_to_file,
)


def build_note(note_id: int = 1) -> dict:
    """Create a saved-shape note."""
    return {
        "id": note_id,
        "created_at": "2026-08-02T12:00:00+00:00",
        "title": "Rent",
        "content": "My landlord raises rent every March.",
    }


def test_save_and_load_notes(db_path):
    original_notes = [build_note()]

    save_notes_to_file(original_notes, db_path)

    loaded_notes = load_notes_from_file(db_path)

    assert loaded_notes == original_notes


def test_load_notes_returns_empty_when_db_missing(tmp_path):
    db_path = tmp_path / "missing.db"

    assert load_notes_from_file(db_path) == []


def test_load_notes_rejects_invalid_database_file(tmp_path):
    db_path = tmp_path / "saved_notes.db"

    db_path.write_text("not a valid sqlite database", encoding="utf-8")

    with pytest.raises(ValueError, match="Failed to load notes"):
        load_notes_from_file(db_path)


def test_save_replaces_all_existing_rows(db_path):
    save_notes_to_file([build_note(1)], db_path)

    second_notes = [build_note(1), build_note(2)]
    save_notes_to_file(second_notes, db_path)

    loaded_notes = load_notes_from_file(db_path)

    assert len(loaded_notes) == 2


def test_save_and_load_multiple_notes_preserves_order(db_path):
    notes = [
        {**build_note(1), "title": "First"},
        {**build_note(2), "title": "Second"},
    ]

    save_notes_to_file(notes, db_path)

    loaded_notes = load_notes_from_file(db_path)

    assert [note["title"] for note in loaded_notes] == ["First", "Second"]
