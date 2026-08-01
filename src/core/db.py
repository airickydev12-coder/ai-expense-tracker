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

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    balance TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    amount TEXT NOT NULL,
    due_day INTEGER NOT NULL,
    is_paid INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS budgets (
    category TEXT PRIMARY KEY,
    "limit" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS debts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    balance TEXT NOT NULL,
    interest_rate REAL NOT NULL,
    minimum_payment TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    amount TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    amount TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    target_amount TEXT NOT NULL,
    current_amount TEXT NOT NULL
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
"""


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """
    Open a SQLite connection configured for the application's needs.

    Ensures the schema exists on every connection so repositories never see
    a "no such table" error on a fresh or missing database file.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)

    return connection


def initialize_database(db_path: Path = DB_PATH) -> None:
    """Create all application tables if they do not already exist."""
    try:
        with get_connection(db_path):
            pass
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to initialize database: {db_path}") from error
