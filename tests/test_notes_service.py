from datetime import datetime, timezone

from src.financial.coach.notes_service import (
    add_note,
    clear_notes,
    delete_note,
    get_notes,
    load_notes,
)
from src.financial.users.repository import create_user

USER_ID = 1


def setup_function():
    """Clear saved notes before each service test."""
    clear_notes()


def teardown_function():
    """Clear saved notes after each service test."""
    clear_notes()


def _create_user(db_path, username: str = "alice") -> None:
    """Insert a throwaway user row so notes' FK constraint is satisfied."""
    create_user(username, f"{username}@example.com", "hash", db_path)


def test_add_note_stamps_created_at(tmp_path):
    db_path = tmp_path / "saved_notes.db"
    _create_user(db_path)

    load_notes(USER_ID, db_path)

    note = add_note(
        USER_ID,
        title="Rent",
        content="My landlord raises rent every March.",
        db_path=db_path,
        now=datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc),
    )

    assert note["id"] == 1
    assert note["created_at"] == "2026-08-02T12:00:00+00:00"
    assert note["title"] == "Rent"
    assert len(get_notes(USER_ID)) == 1
    assert db_path.exists()


def test_add_multiple_notes_assigns_unique_ids(tmp_path):
    db_path = tmp_path / "saved_notes.db"
    _create_user(db_path)

    load_notes(USER_ID, db_path)

    first = add_note(USER_ID, title="First", content="First content.", db_path=db_path)
    second = add_note(USER_ID, title="Second", content="Second content.", db_path=db_path)

    assert first["id"] == 1
    assert second["id"] == 2


def test_add_note_is_restored_after_reload(tmp_path):
    db_path = tmp_path / "saved_notes.db"
    _create_user(db_path)

    load_notes(USER_ID, db_path)
    add_note(USER_ID, title="Rent", content="Rent content.", db_path=db_path)

    clear_notes()

    load_notes(USER_ID, db_path)

    notes = get_notes(USER_ID)

    assert len(notes) == 1
    assert notes[0]["title"] == "Rent"


def test_delete_note_removes_it(tmp_path):
    db_path = tmp_path / "saved_notes.db"
    _create_user(db_path)

    load_notes(USER_ID, db_path)
    note = add_note(USER_ID, title="Rent", content="Rent content.", db_path=db_path)

    deleted = delete_note(USER_ID, note["id"], db_path=db_path)

    assert deleted is not None
    assert deleted["title"] == "Rent"
    assert get_notes(USER_ID) == []

    clear_notes()
    load_notes(USER_ID, db_path)
    assert get_notes(USER_ID) == []


def test_delete_missing_note_returns_none(tmp_path):
    db_path = tmp_path / "saved_notes.db"
    _create_user(db_path)

    load_notes(USER_ID, db_path)

    assert delete_note(USER_ID, 999, db_path=db_path) is None


def test_get_notes_returns_copy(tmp_path):
    db_path = tmp_path / "saved_notes.db"
    _create_user(db_path)

    load_notes(USER_ID, db_path)
    add_note(USER_ID, title="Rent", content="Rent content.", db_path=db_path)

    returned_notes = get_notes(USER_ID)
    returned_notes.clear()

    assert len(get_notes(USER_ID)) == 1


def test_notes_are_isolated_per_user(tmp_path):
    db_path = tmp_path / "saved_notes.db"
    _create_user(db_path, "alice")
    _create_user(db_path, "bob")

    add_note(1, title="User 1 note", content="Content.", db_path=db_path)
    add_note(2, title="User 2 note", content="Content.", db_path=db_path)

    user_one_notes = get_notes(1, db_path=db_path)
    user_two_notes = get_notes(2, db_path=db_path)

    assert len(user_one_notes) == 1
    assert user_one_notes[0]["title"] == "User 1 note"
    assert len(user_two_notes) == 1
    assert user_two_notes[0]["title"] == "User 2 note"
