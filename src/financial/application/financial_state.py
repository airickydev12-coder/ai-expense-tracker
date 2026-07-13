from src.financial.accounts.service import (
    get_accounts,
    load_accounts,
)
from src.financial.bills.service import (
    get_bills,
    load_bills,
)
from src.financial.budgets.service import (
    get_budgets,
    load_budgets,
)
from src.financial.debt.service import (
    get_debts,
    load_debts,
)
from src.financial.engine.financial_engine import (
    build_financial_snapshot,
)
from src.financial.expenses.service import (
    get_expenses,
    load_expenses,
)
from src.financial.goals.service import (
    get_goals,
    load_goals,
)
from src.financial.history.models import FinancialSnapshotRecord
from src.financial.history.service import (
    load_history,
    record_snapshot,
)
from src.financial.income.service import (
    get_income_entries,
    load_income,
)
from src.financial.recommendations.history_service import (
    load_recommendation_history,
)


def load_financial_state() -> None:
    """Load all persisted financial application state."""
    load_expenses()
    load_budgets()
    load_income()
    load_accounts()
    load_goals()
    load_debts()
    load_bills()
    load_recommendation_history()
    load_history()


def get_financial_state() -> dict:
    """Return the current in-memory financial state."""
    return {
        "income_entries": get_income_entries(),
        "expenses": get_expenses(),
        "budgets": get_budgets(),
        "accounts": get_accounts(),
        "goals": get_goals(),
        "debts": get_debts(),
        "bills": get_bills(),
    }


def build_current_financial_snapshot(
    current_day: int | None = None,
) -> dict:
    """Build a snapshot from current in-memory financial data."""
    state = get_financial_state()

    return build_financial_snapshot(
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
    current_day: int | None = None,
) -> tuple[dict, FinancialSnapshotRecord]:
    """Build, record, and return the current financial snapshot."""
    snapshot = build_current_financial_snapshot(
        current_day=current_day
    )

    record = record_snapshot(snapshot)

    return snapshot, record