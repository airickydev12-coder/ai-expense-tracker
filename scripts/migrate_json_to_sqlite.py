"""
One-time migration: copy existing data/*.json content into the new SQLite
database (data/app.db) for all 12 domains converted in Phase 3.

The original JSON files are left untouched. Safe to re-run: each domain's
save_X_to_file() replaces all rows in its table, so re-running this script
just re-imports the same source JSON again.

Run from the repo root as a module (so `src` resolves on sys.path):

    .venv/Scripts/python.exe -m scripts.migrate_json_to_sqlite
"""

from __future__ import annotations

import json
from pathlib import Path

from src.core.config import (
    ACCOUNTS_FILE,
    BILLS_FILE,
    BUDGET_FILE,
    DATA_FILE,
    DB_PATH,
    DEBTS_FILE,
    GOAL_LEDGER_FILE,
    GOAL_PLANNING_REQUESTS_FILE,
    GOALS_FILE,
    HISTORY_FILE,
    INCOME_FILE,
    RECOMMENDATION_HISTORY_FILE,
    SCENARIO_WORKSPACE_FILE,
)
from src.core.db import initialize_database
from src.financial.accounts.models import Account
from src.financial.accounts.repository import save_accounts_to_file
from src.financial.bills.models import Bill
from src.financial.bills.repository import save_bills_to_file
from src.financial.budgets.models import Budget
from src.financial.budgets.repository import save_budgets_to_file
from src.financial.debt.models import Debt
from src.financial.debt.repository import save_debts_to_file
from src.financial.expenses.models import Expense
from src.financial.expenses.repository import save_expenses_to_file
from src.financial.goal_ledger.models import GoalLedgerEntry
from src.financial.goal_ledger.repository import save_goal_ledger_to_file
from src.financial.goals.models import Goal
from src.financial.goals.repository import (
    load_goals_from_file,
    save_goals_to_file,
)
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.repository import save_history_to_file
from src.financial.income.models import Income
from src.financial.income.repository import save_income_to_file
from src.financial.planning.repository import (
    _request_from_record,
    save_goal_planning_requests_to_file,
)
from src.financial.recommendations.history import RecommendationRecord
from src.financial.recommendations.history_repository import (
    save_recommendation_history_to_file,
)
from src.financial.scenarios.workspace_repository import (
    _decimal_object_hook,
    _result_from_dict,
    save_workspace_to_file,
)


def _read_json_list(file_path: Path) -> list[dict]:
    """Read a legacy JSON data file, returning [] if it doesn't exist."""
    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    if not isinstance(raw_data, list):
        raise ValueError(f"{file_path} does not contain a JSON list.")

    return raw_data


def _report(source_file: Path, count: int) -> None:
    print(f"Migrated {count} record(s) from {source_file.name} -> {DB_PATH.name}")


def migrate() -> None:
    """Import every domain's legacy JSON file into the SQLite database."""
    initialize_database()

    accounts = [Account.from_dict(item) for item in _read_json_list(ACCOUNTS_FILE)]
    save_accounts_to_file(accounts)
    _report(ACCOUNTS_FILE, len(accounts))

    bills = [Bill.from_dict(item) for item in _read_json_list(BILLS_FILE)]
    save_bills_to_file(bills)
    _report(BILLS_FILE, len(bills))

    budgets = [Budget.from_dict(item) for item in _read_json_list(BUDGET_FILE)]
    save_budgets_to_file(budgets)
    _report(BUDGET_FILE, len(budgets))

    debts = [Debt.from_dict(item) for item in _read_json_list(DEBTS_FILE)]
    save_debts_to_file(debts)
    _report(DEBTS_FILE, len(debts))

    expenses = [Expense.from_dict(item) for item in _read_json_list(DATA_FILE)]
    save_expenses_to_file(expenses)
    _report(DATA_FILE, len(expenses))

    income_entries = [Income.from_dict(item) for item in _read_json_list(INCOME_FILE)]
    save_income_to_file(income_entries)
    _report(INCOME_FILE, len(income_entries))

    goals = [Goal.from_dict(item) for item in _read_json_list(GOALS_FILE)]
    save_goals_to_file(goals)
    _report(GOALS_FILE, len(goals))

    history = [
        FinancialSnapshotRecord.from_dict(item)
        for item in _read_json_list(HISTORY_FILE)
    ]
    save_history_to_file(history)
    _report(HISTORY_FILE, len(history))

    recommendation_history = [
        RecommendationRecord.from_dict(item)
        for item in _read_json_list(RECOMMENDATION_HISTORY_FILE)
    ]
    save_recommendation_history_to_file(recommendation_history)
    _report(RECOMMENDATION_HISTORY_FILE, len(recommendation_history))

    migrated_goals = load_goals_from_file()
    goals_by_id = {goal.id: goal for goal in migrated_goals}
    planning_requests = {
        request.goal.id: request
        for request in (
            _request_from_record(record, goals_by_id=goals_by_id)
            for record in _read_json_list(GOAL_PLANNING_REQUESTS_FILE)
        )
        if request is not None
    }
    save_goal_planning_requests_to_file(planning_requests)
    _report(GOAL_PLANNING_REQUESTS_FILE, len(planning_requests))

    workspace_results = [
        _result_from_dict(item)
        for item in _read_tagged_decimal_json_list(SCENARIO_WORKSPACE_FILE)
    ]
    save_workspace_to_file(workspace_results)
    _report(SCENARIO_WORKSPACE_FILE, len(workspace_results))

    ledger_entries = [
        GoalLedgerEntry.from_dict(item)
        for item in _read_goal_ledger_entries(GOAL_LEDGER_FILE)
    ]
    save_goal_ledger_to_file(ledger_entries)
    _report(GOAL_LEDGER_FILE, len(ledger_entries))


def _read_tagged_decimal_json_list(file_path: Path) -> list[dict]:
    """Read a legacy JSON list where Decimal values are tagged for restore."""
    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8") as file:
        raw_data = json.load(file, object_hook=_decimal_object_hook)

    if not isinstance(raw_data, list):
        raise ValueError(f"{file_path} does not contain a JSON list.")

    return raw_data


def _read_goal_ledger_entries(file_path: Path) -> list[dict]:
    """Read the legacy goal-ledger document's entries list."""
    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8") as file:
        raw_document = json.load(file)

    if not isinstance(raw_document, dict):
        raise ValueError(f"{file_path} does not contain a JSON object.")

    entries = raw_document.get("entries", [])

    if not isinstance(entries, list):
        raise ValueError(f"{file_path} entries must be a JSON list.")

    return entries


if __name__ == "__main__":
    migrate()
