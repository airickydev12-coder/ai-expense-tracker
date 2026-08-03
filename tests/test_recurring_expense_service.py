import contextlib
from datetime import date
from decimal import Decimal

from src.core.db import clear_test_database, initialize_database, set_test_database
from src.financial.expenses.service import expenses as _expenses
from src.financial.recurring_expenses.models import RecurrenceFrequency
from src.financial.recurring_expenses.service import (
    add_recurring_expense_template,
    delete_recurring_expense_template,
    generate_due_expenses,
    get_next_recurring_expense_template_id,
    get_recurring_expense_template_by_id,
    get_recurring_expense_templates,
    load_recurring_expense_templates,
    recurring_expense_templates,
    update_recurring_expense_template,
)
from src.financial.shared.categories import ExpenseCategory

USER_ID = 1


@contextlib.contextmanager
def _isolated_test_database(tmp_path):
    """Redirect all SQLite writes to a throwaway DB for the duration of a test."""
    test_db_path = tmp_path / "test_recurring_expenses.db"
    initialize_database(test_db_path)
    set_test_database(test_db_path)
    try:
        yield
    finally:
        clear_test_database()


def setup_function():
    """Clear recurring expense template and expense state before every test."""
    recurring_expense_templates.clear()
    _expenses.clear()


def test_add_recurring_expense_template(tmp_path):
    file_path = tmp_path / "recurring.db"

    template = add_recurring_expense_template(
        user_id=USER_ID,
        name="Streaming Subscription",
        category=ExpenseCategory.ENTERTAINMENT,
        amount=Decimal("15.99"),
        frequency=RecurrenceFrequency.MONTHLY,
        next_occurrence=date(2026, 9, 1),
        file_path=file_path,
    )

    assert template.id == 1
    assert template.name == "Streaming Subscription"
    assert template.is_active is True
    assert file_path.exists()


def test_add_multiple_templates_assigns_unique_ids(tmp_path):
    file_path = tmp_path / "recurring.db"

    first = add_recurring_expense_template(
        user_id=USER_ID,
        name="Streaming Subscription",
        category=ExpenseCategory.ENTERTAINMENT,
        amount=Decimal("15.99"),
        frequency=RecurrenceFrequency.MONTHLY,
        next_occurrence=date(2026, 9, 1),
        file_path=file_path,
    )

    second = add_recurring_expense_template(
        user_id=USER_ID,
        name="Gym Membership",
        category=ExpenseCategory.HEALTHCARE,
        amount=Decimal("40.00"),
        frequency=RecurrenceFrequency.WEEKLY,
        next_occurrence=date(2026, 8, 10),
        file_path=file_path,
    )

    assert first.id == 1
    assert second.id == 2
    assert get_next_recurring_expense_template_id(USER_ID, file_path) == 3


def test_get_recurring_expense_templates_returns_copy(tmp_path):
    file_path = tmp_path / "recurring.db"

    add_recurring_expense_template(
        user_id=USER_ID,
        name="Streaming Subscription",
        category=ExpenseCategory.ENTERTAINMENT,
        amount=Decimal("15.99"),
        frequency=RecurrenceFrequency.MONTHLY,
        next_occurrence=date(2026, 9, 1),
        file_path=file_path,
    )

    returned = get_recurring_expense_templates(USER_ID, file_path)
    returned.clear()

    assert len(recurring_expense_templates[USER_ID]) == 1


def test_get_recurring_expense_template_by_id_returns_none(tmp_path):
    file_path = tmp_path / "recurring.db"

    assert get_recurring_expense_template_by_id(USER_ID, 999, file_path) is None


def test_update_recurring_expense_template(tmp_path):
    file_path = tmp_path / "recurring.db"

    template = add_recurring_expense_template(
        user_id=USER_ID,
        name="Streaming Subscription",
        category=ExpenseCategory.ENTERTAINMENT,
        amount=Decimal("15.99"),
        frequency=RecurrenceFrequency.MONTHLY,
        next_occurrence=date(2026, 9, 1),
        file_path=file_path,
    )

    updated = update_recurring_expense_template(
        user_id=USER_ID,
        template_id=template.id,
        amount=Decimal("17.99"),
        is_active=False,
        file_path=file_path,
    )

    assert updated is not None
    assert updated.amount == Decimal("17.99")
    assert updated.is_active is False
    assert updated.name == "Streaming Subscription"


def test_update_recurring_expense_template_returns_none_when_missing(tmp_path):
    file_path = tmp_path / "recurring.db"

    assert (
        update_recurring_expense_template(
            user_id=USER_ID,
            template_id=999,
            amount=Decimal("1.00"),
            file_path=file_path,
        )
        is None
    )


def test_delete_recurring_expense_template(tmp_path):
    file_path = tmp_path / "recurring.db"

    template = add_recurring_expense_template(
        user_id=USER_ID,
        name="Streaming Subscription",
        category=ExpenseCategory.ENTERTAINMENT,
        amount=Decimal("15.99"),
        frequency=RecurrenceFrequency.MONTHLY,
        next_occurrence=date(2026, 9, 1),
        file_path=file_path,
    )

    deleted = delete_recurring_expense_template(
        USER_ID,
        template.id,
        file_path=file_path,
    )

    assert deleted == template
    assert get_recurring_expense_templates(USER_ID, file_path) == []


def test_delete_recurring_expense_template_returns_none_when_missing(tmp_path):
    file_path = tmp_path / "recurring.db"

    assert (
        delete_recurring_expense_template(
            USER_ID,
            999,
            file_path=file_path,
        )
        is None
    )


def test_load_recurring_expense_templates_restores_saved_templates(tmp_path):
    file_path = tmp_path / "recurring.db"

    add_recurring_expense_template(
        user_id=USER_ID,
        name="Streaming Subscription",
        category=ExpenseCategory.ENTERTAINMENT,
        amount=Decimal("15.99"),
        frequency=RecurrenceFrequency.MONTHLY,
        next_occurrence=date(2026, 9, 1),
        file_path=file_path,
    )

    recurring_expense_templates.clear()

    load_recurring_expense_templates(USER_ID, file_path)

    loaded = get_recurring_expense_templates(USER_ID, file_path)

    assert len(loaded) == 1
    assert loaded[0].name == "Streaming Subscription"


def test_generate_due_expenses_creates_expense_and_advances_occurrence(tmp_path):
    with _isolated_test_database(tmp_path):
        add_recurring_expense_template(
            user_id=USER_ID,
            name="Streaming Subscription",
            category=ExpenseCategory.ENTERTAINMENT,
            amount=Decimal("15.99"),
            frequency=RecurrenceFrequency.MONTHLY,
            next_occurrence=date(2026, 9, 1),
        )

        generated = generate_due_expenses(USER_ID, as_of=date(2026, 9, 1))

        assert len(generated) == 1
        assert generated[0].name == "Streaming Subscription"
        assert generated[0].amount == Decimal("15.99")

        template = get_recurring_expense_template_by_id(USER_ID, 1)
        assert template is not None
        assert template.next_occurrence == date(2026, 10, 1)


def test_generate_due_expenses_skips_expenses_not_yet_due(tmp_path):
    with _isolated_test_database(tmp_path):
        add_recurring_expense_template(
            user_id=USER_ID,
            name="Streaming Subscription",
            category=ExpenseCategory.ENTERTAINMENT,
            amount=Decimal("15.99"),
            frequency=RecurrenceFrequency.MONTHLY,
            next_occurrence=date(2026, 12, 1),
        )

        generated = generate_due_expenses(USER_ID, as_of=date(2026, 9, 1))

        assert generated == []


def test_generate_due_expenses_skips_inactive_templates(tmp_path):
    with _isolated_test_database(tmp_path):
        add_recurring_expense_template(
            user_id=USER_ID,
            name="Streaming Subscription",
            category=ExpenseCategory.ENTERTAINMENT,
            amount=Decimal("15.99"),
            frequency=RecurrenceFrequency.MONTHLY,
            next_occurrence=date(2026, 9, 1),
            is_active=False,
        )

        generated = generate_due_expenses(USER_ID, as_of=date(2026, 9, 1))

        assert generated == []


def test_generate_due_expenses_catches_up_multiple_missed_periods(tmp_path):
    with _isolated_test_database(tmp_path):
        add_recurring_expense_template(
            user_id=USER_ID,
            name="Streaming Subscription",
            category=ExpenseCategory.ENTERTAINMENT,
            amount=Decimal("15.99"),
            frequency=RecurrenceFrequency.MONTHLY,
            next_occurrence=date(2026, 6, 1),
        )

        generated = generate_due_expenses(USER_ID, as_of=date(2026, 9, 1))

        assert len(generated) == 4

        template = get_recurring_expense_template_by_id(USER_ID, 1)
        assert template is not None
        assert template.next_occurrence == date(2026, 10, 1)
