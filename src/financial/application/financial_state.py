from src.financial.accounts.service import get_accounts
from src.financial.bills.service import get_bills
from src.financial.budgets.service import get_budgets
from src.financial.debt.service import get_debts
from src.financial.engine.financial_engine import build_financial_snapshot
from src.financial.expenses.service import get_expenses
from src.financial.goals.service import get_goals
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.service import record_snapshot
from src.financial.income.service import get_income_entries


def get_financial_state(user_id: int) -> dict:
    """Return this user's current in-memory financial state.

    Each getter lazily loads that user's own data on first access -- there
    is no separate eager "load everything at startup" step (see
    src/api/main.py's lifespan): a request that only touches one domain
    never pays the cost of loading every other domain too.
    """
    return {
        "income_entries": get_income_entries(user_id),
        "expenses": get_expenses(user_id),
        "budgets": get_budgets(user_id),
        "accounts": get_accounts(user_id),
        "goals": get_goals(user_id),
        "debts": get_debts(user_id),
        "bills": get_bills(user_id),
    }


def build_current_financial_snapshot(
    user_id: int,
    current_day: int | None = None,
) -> dict:
    """Build a snapshot from a user's current in-memory financial data."""
    state = get_financial_state(user_id)

    return build_financial_snapshot(
        user_id,
        income_entries=state["income_entries"],
        expenses=state["expenses"],
        budgets=state["budgets"],
        accounts=state["accounts"],
        goals=state["goals"],
        debts=state["debts"],
        bills=state["bills"],
        current_day=current_day,
    )


def record_current_financial_snapshot(
    user_id: int,
    current_day: int | None = None,
) -> tuple[dict, FinancialSnapshotRecord]:
    """Build, record, and return a user's current financial snapshot."""
    snapshot = build_current_financial_snapshot(user_id, current_day=current_day)

    record = record_snapshot(user_id, snapshot)

    return snapshot, record
