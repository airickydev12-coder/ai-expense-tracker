from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from src.core.config import DB_PATH
from src.core.logging import get_logger
from src.financial.expenses.models import Expense
from src.financial.expenses.service import add_expense
from src.financial.goals.projections import add_months
from src.financial.recurring_expenses.models import (
    RecurrenceFrequency,
    RecurringExpenseTemplate,
)
from src.financial.recurring_expenses.repository import (
    load_recurring_expense_templates_from_file,
    save_recurring_expense_templates_to_file,
)
from src.financial.shared.categories import ExpenseCategory

logger = get_logger(__name__)

recurring_expense_templates: dict[int, list[RecurringExpenseTemplate]] = {}


def _ensure_loaded(user_id: int, file_path: Path = DB_PATH) -> None:
    """Lazily load a user's recurring expense templates into the cache on first access."""
    if user_id not in recurring_expense_templates:
        recurring_expense_templates[user_id] = load_recurring_expense_templates_from_file(
            user_id, file_path
        )


def load_recurring_expense_templates(
    user_id: int,
    file_path: Path = DB_PATH,
) -> None:
    """Force-reload a user's recurring expense templates from the repository."""
    recurring_expense_templates[user_id] = load_recurring_expense_templates_from_file(
        user_id, file_path
    )


def save_recurring_expense_templates(
    user_id: int,
    file_path: Path = DB_PATH,
) -> None:
    """Save a user's recurring expense templates using the repository."""
    save_recurring_expense_templates_to_file(
        recurring_expense_templates[user_id],
        user_id,
        file_path,
    )


def get_recurring_expense_templates(
    user_id: int,
    file_path: Path = DB_PATH,
) -> list[RecurringExpenseTemplate]:
    """Return a copy of all of this user's recurring expense templates."""
    _ensure_loaded(user_id, file_path)
    return recurring_expense_templates[user_id].copy()


def get_recurring_expense_template_by_id(
    user_id: int,
    template_id: int,
    file_path: Path = DB_PATH,
) -> RecurringExpenseTemplate | None:
    """Return one of this user's recurring expense templates by ID."""
    _ensure_loaded(user_id, file_path)

    for template in recurring_expense_templates[user_id]:
        if template.id == template_id:
            return template

    return None


def get_next_recurring_expense_template_id(user_id: int, file_path: Path = DB_PATH) -> int:
    """Return the next available recurring expense template ID for this user."""
    _ensure_loaded(user_id, file_path)
    user_templates = recurring_expense_templates[user_id]
    if not user_templates:
        return 1

    return max(template.id for template in user_templates) + 1


def add_recurring_expense_template(
    user_id: int,
    name: str,
    category: ExpenseCategory,
    amount: Decimal,
    frequency: RecurrenceFrequency,
    next_occurrence: date,
    is_active: bool = True,
    file_path: Path = DB_PATH,
) -> RecurringExpenseTemplate:
    """Create and save a recurring expense template for this user."""
    _ensure_loaded(user_id, file_path)

    template = RecurringExpenseTemplate(
        id=get_next_recurring_expense_template_id(user_id, file_path),
        name=name,
        category=category,
        amount=amount,
        frequency=frequency,
        next_occurrence=next_occurrence,
        is_active=is_active,
    )

    recurring_expense_templates[user_id].append(template)
    save_recurring_expense_templates(user_id, file_path)

    logger.info(
        "Added recurring expense template %d (%s) for user %d",
        template.id,
        template.name,
        user_id,
    )

    return template


def update_recurring_expense_template(
    user_id: int,
    template_id: int,
    name: str | None = None,
    category: ExpenseCategory | None = None,
    amount: Decimal | None = None,
    frequency: RecurrenceFrequency | None = None,
    next_occurrence: date | None = None,
    is_active: bool | None = None,
    file_path: Path = DB_PATH,
) -> RecurringExpenseTemplate | None:
    """Update one of this user's existing recurring expense templates by ID."""
    _ensure_loaded(user_id, file_path)

    template = get_recurring_expense_template_by_id(user_id, template_id, file_path)

    if template is None:
        return None

    updated_template = RecurringExpenseTemplate(
        id=template.id,
        name=(name.strip() if name is not None else template.name),
        category=(category if category is not None else template.category),
        amount=(amount if amount is not None else template.amount),
        frequency=(frequency if frequency is not None else template.frequency),
        next_occurrence=(
            next_occurrence if next_occurrence is not None else template.next_occurrence
        ),
        is_active=(is_active if is_active is not None else template.is_active),
    )

    template_index = recurring_expense_templates[user_id].index(template)
    recurring_expense_templates[user_id][template_index] = updated_template

    save_recurring_expense_templates(user_id, file_path)

    logger.info(
        "Updated recurring expense template %d for user %d",
        template_id,
        user_id,
    )

    return updated_template


def delete_recurring_expense_template(
    user_id: int,
    template_id: int,
    file_path: Path = DB_PATH,
) -> RecurringExpenseTemplate | None:
    """Delete one of this user's recurring expense templates by ID."""
    _ensure_loaded(user_id, file_path)

    for index, template in enumerate(recurring_expense_templates[user_id]):
        if template.id == template_id:
            deleted_template = recurring_expense_templates[user_id].pop(index)
            save_recurring_expense_templates(user_id, file_path)
            logger.info(
                "Deleted recurring expense template %d for user %d",
                template_id,
                user_id,
            )
            return deleted_template

    return None


def _advance_occurrence(
    current: date,
    frequency: RecurrenceFrequency,
) -> date:
    """Return the next occurrence date after `current` for the given frequency."""
    if frequency == RecurrenceFrequency.WEEKLY:
        return current + timedelta(days=7)

    if frequency == RecurrenceFrequency.BIWEEKLY:
        return current + timedelta(days=14)

    if frequency == RecurrenceFrequency.YEARLY:
        return add_months(current, 12)

    return add_months(current, 1)


def generate_due_expenses(
    user_id: int,
    as_of: date | None = None,
    file_path: Path = DB_PATH,
) -> list[Expense]:
    """
    Generate real expenses for every one of this user's active templates that is due.

    A template due more than one period ago generates one expense per
    missed period (catch-up semantics), advancing its next occurrence
    each time, so a template checked after several months of inactivity
    doesn't silently skip the missed periods.
    """
    _ensure_loaded(user_id, file_path)

    effective_date = as_of if as_of is not None else date.today()

    generated_expenses: list[Expense] = []
    templates_changed = False

    for template in recurring_expense_templates[user_id]:
        if not template.is_active:
            continue

        while template.next_occurrence <= effective_date:
            expense = add_expense(
                user_id=user_id,
                name=template.name,
                category=template.category,
                amount=template.amount,
            )
            generated_expenses.append(expense)

            template.next_occurrence = _advance_occurrence(
                template.next_occurrence,
                template.frequency,
            )
            templates_changed = True

    if templates_changed:
        save_recurring_expense_templates(user_id, file_path)

    logger.info(
        "Generated %d expense(s) from recurring templates for user %d as of %s",
        len(generated_expenses),
        user_id,
        effective_date.isoformat(),
    )

    return generated_expenses
