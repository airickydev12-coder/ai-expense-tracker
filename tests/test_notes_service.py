from datetime import datetime, timezone

from src.financial.coach.notes_service import (
    add_note,
    clear_notes,
    delete_note,
    get_notes,
    load_notes,
)


def setup_function():
    """Clear saved notes before each service test."""
    clear_notes()


def teardown_function():
    """Clear saved notes after each service test."""
    clear_notes()


def test_add_note_stamps_created_at(tmp_path):
    file_path = tmp_path / "saved_notes.db"

    load_notes(file_path)

    note = add_note(
        title="Rent",
        content="My landlord raises rent every March.",
        file_path=file_path,
        now=datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc),
    )

    assert note["id"] == 1
    assert note["created_at"] == "2026-08-02T12:00:00+00:00"
    assert note["title"] == "Rent"
    assert len(get_notes()) == 1
    assert file_path.exists()


def test_add_multiple_notes_assigns_unique_ids(tmp_path):
    file_path = tmp_path / "saved_notes.db"

    load_notes(file_path)

    first = add_note(title="First", content="First content.", file_path=file_path)
    second = add_note(title="Second", content="Second content.", file_path=file_path)

    assert first["id"] == 1
    assert second["id"] == 2


def test_add_note_is_restored_after_reload(tmp_path):
    file_path = tmp_path / "saved_notes.db"

    load_notes(file_path)
    add_note(title="Rent", content="Rent content.", file_path=file_path)

    clear_notes()
    assert get_notes() == []

    load_notes(file_path)

    notes = get_notes()

    assert len(notes) == 1
    assert notes[0]["title"] == "Rent"


def test_delete_note_removes_it(tmp_path):
    file_path = tmp_path / "saved_notes.db"

    load_notes(file_path)
    note = add_note(title="Rent", content="Rent content.", file_path=file_path)

    deleted = delete_note(note["id"], file_path=file_path)

    assert deleted is not None
    assert deleted["title"] == "Rent"
    assert get_notes() == []

    load_notes(file_path)
    assert get_notes() == []


def test_delete_missing_note_returns_none(tmp_path):
    file_path = tmp_path / "saved_notes.db"

    load_notes(file_path)

    assert delete_note(999, file_path=file_path) is None


def test_get_notes_returns_copy(tmp_path):
    file_path = tmp_path / "saved_notes.db"

    load_notes(file_path)
    add_note(title="Rent", content="Rent content.", file_path=file_path)

    returned_notes = get_notes()
    returned_notes.clear()

    assert len(get_notes()) == 1
