from src.core.logging import get_logger

logger = get_logger(__name__)


def log_expense_added(expense) -> None:
    logger.info("Expense added: %s", expense.name)


def log_income_added(income) -> None:
    logger.info("Income added: %s", income.source)
