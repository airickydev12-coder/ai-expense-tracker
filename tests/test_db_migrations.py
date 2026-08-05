"""Tests for src/core/db.py's one-time schema migrations."""

import sqlite3

import pytest

from src.core.db import get_connection

_USERS_TABLE_DDL = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_OLD_SHAPE_EXPENSES_DDL = """
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    amount TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id)
)
"""


def _create_old_shape_database(db_path) -> None:
    """Build a database in the pre-Stage-B shape: expenses has a plain,
    already-backfilled user_id column that isn't part of the primary key
    yet — exactly the state data/app.db was in after Stage A."""
    connection = sqlite3.connect(db_path)
    connection.execute(_USERS_TABLE_DDL)
    connection.execute(
        "INSERT INTO users (id, username, email, password_hash, created_at, updated_at) "
        "VALUES (7, 'alice', 'alice@example.com', 'hash', '2026-01-01T00:00:00', '2026-01-01T00:00:00')"
    )
    connection.execute(_OLD_SHAPE_EXPENSES_DDL)
    connection.execute(
        "INSERT INTO expenses (id, name, category, amount, user_id) "
        "VALUES (1, 'Coffee', 'DINING', '4.50', 7)"
    )
    connection.commit()
    connection.close()


def test_composite_pk_migration_preserves_data_and_adds_user_id_to_pk(tmp_path) -> None:
    db_path = tmp_path / "legacy.db"
    _create_old_shape_database(db_path)

    with get_connection(db_path) as connection:
        rows = connection.execute(
            "SELECT id, name, category, amount, user_id FROM expenses"
        ).fetchall()
        pk_by_column = {
            row["name"]: row["pk"] for row in connection.execute("PRAGMA table_info(expenses)")
        }

    assert len(rows) == 1
    assert rows[0]["name"] == "Coffee"
    assert rows[0]["user_id"] == 7
    assert pk_by_column["id"] > 0
    assert pk_by_column["user_id"] > 0


def test_composite_pk_migration_is_idempotent(tmp_path) -> None:
    db_path = tmp_path / "legacy.db"
    _create_old_shape_database(db_path)

    with get_connection(db_path):
        pass  # first connection performs the migration

    with get_connection(db_path) as connection:
        rows = connection.execute("SELECT * FROM expenses").fetchall()

    assert len(rows) == 1


def test_composite_pk_migration_leaves_original_table_intact_on_failure(tmp_path) -> None:
    """A row with a NULL user_id (predating a backfill) makes the copy step
    violate the new NOT NULL constraint. The migration must roll back
    completely rather than leaving the table renamed-aside with an empty
    new-shape table in its place."""
    db_path = tmp_path / "legacy_unbackfilled.db"
    connection = sqlite3.connect(db_path)
    connection.execute(_USERS_TABLE_DDL)
    connection.execute(_OLD_SHAPE_EXPENSES_DDL)
    connection.execute(
        "INSERT INTO expenses (id, name, category, amount, user_id) "
        "VALUES (1, 'Coffee', 'DINING', '4.50', NULL)"
    )
    connection.commit()
    connection.close()

    with pytest.raises(sqlite3.IntegrityError):
        get_connection(db_path)

    # Original table must still exist, under its original name, with its
    # original data — not renamed aside, not replaced by an empty table.
    raw_connection = sqlite3.connect(db_path)
    raw_connection.row_factory = sqlite3.Row
    tables = {row["name"] for row in raw_connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    rows = raw_connection.execute("SELECT * FROM expenses").fetchall()

    assert "expenses" in tables
    assert "expenses_pre_composite_pk" not in tables
    assert len(rows) == 1
    assert rows[0]["name"] == "Coffee"


def test_fresh_database_never_exercises_migration_branch(tmp_path) -> None:
    """A brand-new database gets the composite-PK shape directly from
    SCHEMA, so the migration's up-front check should already see it as
    migrated and never touch the table at all."""
    db_path = tmp_path / "fresh.db"

    with get_connection(db_path) as connection:
        pk_by_column = {
            row["name"]: row["pk"] for row in connection.execute("PRAGMA table_info(expenses)")
        }

    assert pk_by_column["id"] > 0
    assert pk_by_column["user_id"] > 0


def test_role_column_migration_adds_column_with_default(tmp_path) -> None:
    """An old-shape users table (no role column) gets one added, with
    'user' applied to every pre-existing row."""
    db_path = tmp_path / "legacy_no_role.db"
    _create_old_shape_database(db_path)

    with get_connection(db_path) as connection:
        row = connection.execute("SELECT role FROM users WHERE id = 7").fetchone()

    assert row["role"] == "user"


def test_role_column_migration_is_idempotent(tmp_path) -> None:
    db_path = tmp_path / "legacy_no_role.db"
    _create_old_shape_database(db_path)

    with get_connection(db_path):
        pass  # first connection performs the migration

    with get_connection(db_path) as connection:
        row = connection.execute("SELECT role FROM users WHERE id = 7").fetchone()

    assert row["role"] == "user"


def test_fresh_database_users_table_already_has_role_column(tmp_path) -> None:
    """A brand-new database gets the role column directly from SCHEMA, so
    the migration's up-front check should already see it as present."""
    db_path = tmp_path / "fresh_role.db"

    with get_connection(db_path) as connection:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}

    assert "role" in columns


def test_account_type_column_migration_adds_column_with_default(tmp_path) -> None:
    """An old-shape users table (no account_type column) gets one added,
    defaulting every pre-existing row to 'adult'."""
    db_path = tmp_path / "legacy_no_account_type.db"
    _create_old_shape_database(db_path)

    with get_connection(db_path) as connection:
        row = connection.execute("SELECT account_type FROM users WHERE id = 7").fetchone()

    assert row["account_type"] == "adult"


def test_account_type_column_migration_is_idempotent(tmp_path) -> None:
    db_path = tmp_path / "legacy_no_account_type.db"
    _create_old_shape_database(db_path)

    with get_connection(db_path):
        pass  # first connection performs the migration

    with get_connection(db_path) as connection:
        row = connection.execute("SELECT account_type FROM users WHERE id = 7").fetchone()

    assert row["account_type"] == "adult"


def test_fresh_database_users_table_already_has_account_type_column(tmp_path) -> None:
    db_path = tmp_path / "fresh_account_type.db"

    with get_connection(db_path) as connection:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}

    assert "account_type" in columns


def test_fresh_database_has_household_and_consent_tables(tmp_path) -> None:
    """A brand-new database gets all 5 ADR-007 tables directly from SCHEMA,
    with the right primary-key shape (composite on household_memberships,
    single user_id on learning_profiles)."""
    db_path = tmp_path / "fresh_family_domain.db"

    with get_connection(db_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        membership_pk = [
            row["name"]
            for row in connection.execute("PRAGMA table_info(household_memberships)")
            if row["pk"] > 0
        ]
        learning_profile_pk = [
            row["name"]
            for row in connection.execute("PRAGMA table_info(learning_profiles)")
            if row["pk"] > 0
        ]

    assert {
        "households",
        "household_memberships",
        "guardian_child_relationships",
        "consent_records",
        "learning_profiles",
    } <= tables
    assert set(membership_pk) == {"household_id", "user_id"}
    assert learning_profile_pk == ["user_id"]
