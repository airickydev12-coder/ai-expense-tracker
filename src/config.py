from pathlib import Path

APP_NAME = "Financial Core"
VERSION = "0.5.0"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

DATA_FILE = DATA_DIR / "expenses.json"