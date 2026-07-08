from src.financial.events.bus import event_bus
from src.financial.events.event_types import FinancialEvent
from src.financial.events.handlers import (
    log_expense_added,
    log_income_added,
)


def register_handlers() -> None:
    event_bus.subscribe(
        FinancialEvent.EXPENSE_ADDED,
        log_expense_added,
    )

    event_bus.subscribe(
        FinancialEvent.INCOME_ADDED,
        log_income_added,
    )