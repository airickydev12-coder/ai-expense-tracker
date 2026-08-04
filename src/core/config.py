import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Financial Core"
VERSION = "0.7.0"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
NOTIFICATION_TO_EMAIL = os.getenv("NOTIFICATION_TO_EMAIL")
NOTIFICATION_CHECK_INTERVAL_MINUTES = int(
    os.getenv("NOTIFICATION_CHECK_INTERVAL_MINUTES", "60")
)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-insecure-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
# Short-lived: refresh tokens (below) transparently renew the session, so
# this no longer needs to cover a whole day the way it did before Stage 5
# of the auth hardening backlog added refresh tokens.
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "15"))
REFRESH_TOKEN_EXPIRY_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRY_DAYS", "30"))

LOGIN_LOCKOUT_MAX_ATTEMPTS = int(os.getenv("LOGIN_LOCKOUT_MAX_ATTEMPTS", "5"))
LOGIN_LOCKOUT_WINDOW_MINUTES = int(os.getenv("LOGIN_LOCKOUT_WINDOW_MINUTES", "15"))

PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = int(
    os.getenv("PASSWORD_RESET_TOKEN_EXPIRY_MINUTES", "30")
)
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")

# Tighter than login's lockout: forgot-password abuse (spamming reset emails
# at an address) is lower-frequency but higher-annoyance-per-hit than login
# brute-forcing.
PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS = int(
    os.getenv("PASSWORD_RESET_LOCKOUT_MAX_ATTEMPTS", "3")
)
PASSWORD_RESET_LOCKOUT_WINDOW_MINUTES = int(
    os.getenv("PASSWORD_RESET_LOCKOUT_WINDOW_MINUTES", "60")
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"

DB_PATH = DATA_DIR / "app.db"

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
