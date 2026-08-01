from pathlib import Path

APP_NAME = "Financial Core"
VERSION = "0.7.0"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"

DATA_FILE = DATA_DIR / "expenses.json"
GOALS_FILE = DATA_DIR / "goals.json"
GOAL_PLANNING_REQUESTS_FILE = DATA_DIR / "goal_planning_requests.json"
GOAL_LEDGER_FILE = DATA_DIR / "goal_ledger.json"
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
BILLS_FILE = DATA_DIR / "bills.json"
BUDGET_FILE = DATA_DIR / "budgets.json"
DEBTS_FILE = DATA_DIR / "debts.json"
INCOME_FILE = DATA_DIR / "income.json"
HISTORY_FILE = DATA_DIR / "financial_history.json"
SCENARIO_WORKSPACE_FILE = DATA_DIR / "scenario_workspace.json"
RECOMMENDATION_HISTORY_FILE = DATA_DIR / "recommendation_history.json"
