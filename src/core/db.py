"""
SQLite connection and schema management for the Financial Core application.

Table columns are designed to mirror each domain model's to_dict()/from_dict()
keys exactly, so the domain layer never needs to know it is backed by SQLite.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.exceptions import PersistenceError

_SINGLE_USER_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    email_verified_at TEXT
);

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT
);

CREATE TABLE IF NOT EXISTS email_verification_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    requested_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS admin_audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_user_id INTEGER,
    action TEXT NOT NULL,
    target_type TEXT,
    target_id TEXT,
    reason TEXT,
    request_id TEXT,
    ip_address TEXT,
    metadata TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    attempted_at TEXT NOT NULL,
    succeeded INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT
);

CREATE TABLE IF NOT EXISTS password_reset_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    requested_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL,
    issued_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    user_agent TEXT,
    ip_address TEXT
);

CREATE TABLE IF NOT EXISTS financial_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    total_income TEXT NOT NULL,
    total_expenses TEXT NOT NULL,
    net_cash_flow TEXT NOT NULL,
    total_account_balance TEXT NOT NULL,
    total_goal_progress TEXT NOT NULL,
    total_debt TEXT NOT NULL,
    net_worth TEXT NOT NULL,
    health_score INTEGER NOT NULL,
    health_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS monthly_review_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generated_at TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS goal_ledger_entries (
    entry_id TEXT PRIMARY KEY,
    goal_id INTEGER NOT NULL,
    entry_type TEXT NOT NULL,
    amount TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    source TEXT NOT NULL,
    note TEXT NOT NULL,
    correlation_id TEXT,
    reverses_entry_id TEXT
);
"""

# Tables whose own id/key is assigned by the app itself (a per-list max+1
# counter, or a deterministic/free-text value) rather than by SQLite
# AUTOINCREMENT or a UUID. Once each user's data is isolated, two users'
# rows would collide on an identical id/key unless user_id is part of the
# primary key — so each of these gets a composite (user_id, <original key>)
# PK instead of the single-column PK it had before Stage B. Column order
# matches exactly what Stage A's _ensure_user_id_columns ALTER TABLE
# appended (original columns, then user_id last), so the migration below
# can copy rows with a plain `SELECT *` rather than an explicit column list.
_COMPOSITE_PK_TABLE_SCHEMAS: dict[str, str] = {
    "accounts": """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER NOT NULL,
            name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            balance TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, id)
        );
    """,
    "bills": """
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER NOT NULL,
            name TEXT NOT NULL,
            amount TEXT NOT NULL,
            due_day INTEGER NOT NULL,
            is_paid INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, id)
        );
    """,
    "budgets": """
        CREATE TABLE IF NOT EXISTS budgets (
            category TEXT NOT NULL,
            "limit" TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, category)
        );
    """,
    "debts": """
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER NOT NULL,
            name TEXT NOT NULL,
            balance TEXT NOT NULL,
            interest_rate REAL NOT NULL,
            minimum_payment TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, id)
        );
    """,
    "expenses": """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            amount TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, id)
        );
    """,
    "income": """
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER NOT NULL,
            source TEXT NOT NULL,
            amount TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, id)
        );
    """,
    "goals": """
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER NOT NULL,
            name TEXT NOT NULL,
            target_amount TEXT NOT NULL,
            current_amount TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, id)
        );
    """,
    "recommendation_history": """
        CREATE TABLE IF NOT EXISTS recommendation_history (
            recommendation_key TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            note TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, recommendation_key)
        );
    """,
    "goal_planning_requests": """
        CREATE TABLE IF NOT EXISTS goal_planning_requests (
            goal_id INTEGER NOT NULL,
            target_date TEXT NOT NULL,
            planned_monthly_contribution TEXT NOT NULL,
            priority TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, goal_id)
        );
    """,
    "scenario_workspace": """
        CREATE TABLE IF NOT EXISTS scenario_workspace (
            name TEXT NOT NULL,
            data TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, name)
        );
    """,
    "financial_history_category_totals": """
        CREATE TABLE IF NOT EXISTS financial_history_category_totals (
            timestamp TEXT NOT NULL,
            data TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, timestamp)
        );
    """,
    "saved_notes": """
        CREATE TABLE IF NOT EXISTS saved_notes (
            id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, id)
        );
    """,
    "notification_log": """
        CREATE TABLE IF NOT EXISTS notification_log (
            id INTEGER NOT NULL,
            notification_key TEXT NOT NULL,
            channel TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            status TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, id)
        );
    """,
    "recurring_expense_templates": """
        CREATE TABLE IF NOT EXISTS recurring_expense_templates (
            id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            amount TEXT NOT NULL,
            frequency TEXT NOT NULL,
            next_occurrence TEXT NOT NULL,
            is_active INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, id)
        );
    """,
}

SCHEMA = _SINGLE_USER_SCHEMA + "\n".join(_COMPOSITE_PK_TABLE_SCHEMAS.values())


_NULLABLE_USER_ID_TABLES = [
    "financial_history",
    "monthly_review_history",
    "goal_ledger_entries",
]

_COMPOSITE_PK_TABLES = list(_COMPOSITE_PK_TABLE_SCHEMAS)


def _ensure_user_id_columns(connection: sqlite3.Connection) -> None:
    """Add a nullable user_id column to the DB-assigned-id tables if missing.

    CREATE TABLE IF NOT EXISTS is a no-op on tables that already exist, so a
    new column can't be added by editing SCHEMA alone once a real database
    file exists. This runs an idempotent ALTER TABLE ADD COLUMN for any
    table missing it, mirroring how SCHEMA itself is re-run on every
    connection. Scoped to the 3 tables whose own id/key is already globally
    unique (DB AUTOINCREMENT or a UUID) — the other 14 get user_id baked
    into a composite primary key instead, via _ensure_composite_primary_keys.
    """
    for table in _NULLABLE_USER_ID_TABLES:
        columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
        if "user_id" not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")


def _ensure_role_column(connection: sqlite3.Connection) -> None:
    """Add a role column (default 'user') to `users` if missing.

    Same idempotent-ALTER-TABLE pattern as _ensure_user_id_columns, for the
    same reason: CREATE TABLE IF NOT EXISTS is a no-op once a real database
    file already has a `users` table without this column. SQLite's ALTER
    TABLE ADD COLUMN supports a constant DEFAULT, so every pre-existing row
    gets 'user' applied automatically -- no row is ever left unprotected.
    """
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
    if "role" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")


def _ensure_email_verified_at_column(connection: sqlite3.Connection) -> None:
    """Add an email_verified_at column (default NULL, i.e. unverified) to
    `users` if missing. Same idempotent-ALTER-TABLE pattern as
    _ensure_role_column, for the same reason.
    """
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
    if "email_verified_at" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN email_verified_at TEXT")


def _ensure_refresh_token_metadata_columns(connection: sqlite3.Connection) -> None:
    """Add user_agent/ip_address columns to `refresh_tokens` if missing --
    same idempotent-ALTER-TABLE pattern as _ensure_role_column. Powers the
    self-service active-sessions list (which device/location a session
    belongs to) — existing rows just get NULL for both, same as any
    session issued before this shipped.
    """
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(refresh_tokens)")}
    if "user_agent" not in columns:
        connection.execute("ALTER TABLE refresh_tokens ADD COLUMN user_agent TEXT")
    if "ip_address" not in columns:
        connection.execute("ALTER TABLE refresh_tokens ADD COLUMN ip_address TEXT")


def _table_has_composite_user_pk(connection: sqlite3.Connection, table: str) -> bool:
    """Return whether `table`'s user_id column is already part of its primary key."""
    for row in connection.execute(f"PRAGMA table_info({table})"):
        if row["name"] == "user_id" and row["pk"] > 0:
            return True
    return False


def _ensure_composite_primary_keys(connection: sqlite3.Connection) -> None:
    """Migrate each table in _COMPOSITE_PK_TABLES to a (user_id, <original
    key>) primary key, if not already migrated.

    SQLite can't ALTER a PRIMARY KEY in place, so an already-existing table
    (the real upgraded data/app.db, whose 14 tables gained a plain nullable
    user_id column in Stage A) is migrated by renaming it aside, creating
    the new composite-PK table from _COMPOSITE_PK_TABLE_SCHEMAS, copying
    every row across, and dropping the renamed original. Column order in
    the new schema exactly matches the old ALTER-added order (original
    columns, then user_id last), so `SELECT *` copies correctly without an
    explicit column list.

    A brand-new database (every test, via initialize_database()) never
    exercises the migration branch at all: SCHEMA already declares these
    14 tables in their final composite-PK shape, so this function's
    up-front check finds them already migrated and no-ops immediately.
    """
    for table in _COMPOSITE_PK_TABLES:
        if _table_has_composite_user_pk(connection, table):
            continue

        # SQLite's DDL statements (CREATE/ALTER/DROP) auto-commit immediately
        # unless wrapped in an explicit transaction, so without this BEGIN a
        # failed INSERT (e.g. a row with a NULL user_id that predates the
        # backfill) would leave the table mid-migration: renamed aside with
        # an empty new-shape table in its place, rather than either fully
        # migrated or fully untouched.
        old_table = f"{table}_pre_composite_pk"
        connection.execute("BEGIN")
        try:
            # executescript() (unlike execute()) implicitly COMMITs any
            # pending transaction before running, which would silently
            # defeat this whole BEGIN/ROLLBACK block — use execute() since
            # each schema entry is a single CREATE TABLE statement.
            connection.execute(f"ALTER TABLE {table} RENAME TO {old_table}")
            connection.execute(_COMPOSITE_PK_TABLE_SCHEMAS[table])
            connection.execute(f"INSERT INTO {table} SELECT * FROM {old_table}")
            connection.execute(f"DROP TABLE {old_table}")
            connection.execute("COMMIT")
        except sqlite3.Error:
            connection.execute("ROLLBACK")
            raise


_test_db_path_override: Path | None = None


def set_test_database(db_path: Path) -> None:
    """
    Redirect every caller relying on the default DB_PATH to a test database.

    Only takes effect for callers that didn't explicitly choose a different
    path (e.g. repository unit tests passing their own tmp_path) — those are
    never affected, since this only substitutes the *default* value.
    """
    global _test_db_path_override
    _test_db_path_override = db_path


def clear_test_database() -> None:
    """Stop redirecting the default DB_PATH to a test database."""
    global _test_db_path_override
    _test_db_path_override = None


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """
    Open a SQLite connection configured for the application's needs.

    Ensures the schema exists on every connection so repositories never see
    a "no such table" error on a fresh or missing database file.
    """
    if _test_db_path_override is not None and db_path == DB_PATH:
        db_path = _test_db_path_override

    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    _ensure_role_column(connection)
    _ensure_email_verified_at_column(connection)
    _ensure_refresh_token_metadata_columns(connection)
    _ensure_user_id_columns(connection)
    _ensure_composite_primary_keys(connection)

    return connection


def initialize_database(db_path: Path = DB_PATH) -> None:
    """Create all application tables if they do not already exist."""
    try:
        with get_connection(db_path):
            pass
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to initialize database: {db_path}") from error
