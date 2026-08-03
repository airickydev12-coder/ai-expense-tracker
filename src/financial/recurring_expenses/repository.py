import sqlite3
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.recurring_expenses.models import RecurringExpenseTemplate

logger = get_logger(__name__)


def load_recurring_expense_templates_from_file(
    db_path: Path = DB_PATH,
) -> list[RecurringExpenseTemplate]:
    """Load recurring expense templates from the database."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                """
                SELECT id, name, category, amount, frequency, next_occurrence, is_active
                FROM recurring_expense_templates ORDER BY id
                """
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to load recurring expense templates from {db_path}"
        ) from error

    templates = [RecurringExpenseTemplate.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d recurring expense template(s) from %s",
        len(templates),
        db_path,
    )

    return templates


def save_recurring_expense_templates_to_file(
    templates: list[RecurringExpenseTemplate],
    db_path: Path = DB_PATH,
) -> None:
    """Save recurring expense templates to the database, replacing all existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute("DELETE FROM recurring_expense_templates")
            connection.executemany(
                """
                INSERT INTO recurring_expense_templates
                    (id, name, category, amount, frequency, next_occurrence, is_active)
                VALUES
                    (:id, :name, :category, :amount, :frequency, :next_occurrence, :is_active)
                """,
                [template.to_dict() for template in templates],
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to save recurring expense templates to {db_path}"
        ) from error

    logger.debug(
        "Saved %d recurring expense template(s) to %s",
        len(templates),
        db_path,
    )
