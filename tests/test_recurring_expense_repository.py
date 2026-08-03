from datetime import date
from decimal import Decimal

import pytest

from src.financial.recurring_expenses.models import (
    RecurrenceFrequency,
    RecurringExpenseTemplate,
)
from src.financial.recurring_expenses.repository import (
    load_recurring_expense_templates_from_file,
    save_recurring_expense_templates_to_file,
)
from src.financial.shared.categories import ExpenseCategory


def test_save_and_load_recurring_expense_templates(db_path):
    original_templates = [
        RecurringExpenseTemplate(
            id=1,
            name="Streaming Subscription",
            category=ExpenseCategory.ENTERTAINMENT,
            amount=Decimal("15.99"),
            frequency=RecurrenceFrequency.MONTHLY,
            next_occurrence=date(2026, 9, 1),
        ),
        RecurringExpenseTemplate(
            id=2,
            name="Gym Membership",
            category=ExpenseCategory.HEALTHCARE,
            amount=Decimal("40.00"),
            frequency=RecurrenceFrequency.WEEKLY,
            next_occurrence=date(2026, 8, 10),
            is_active=False,
        ),
    ]

    save_recurring_expense_templates_to_file(
        original_templates,
        1,
        db_path,
    )

    loaded_templates = load_recurring_expense_templates_from_file(
        1,
        db_path,
    )

    assert loaded_templates == original_templates


def test_load_recurring_expense_templates_returns_empty_list_when_db_missing(
    tmp_path,
):
    db_path = tmp_path / "missing_recurring_expenses.db"

    assert load_recurring_expense_templates_from_file(1, db_path) == []


def test_save_recurring_expense_templates_creates_parent_directory(
    tmp_path,
):
    db_path = tmp_path / "nested" / "data" / "recurring_expenses.db"

    templates = [
        RecurringExpenseTemplate(
            id=1,
            name="Streaming Subscription",
            category=ExpenseCategory.ENTERTAINMENT,
            amount=Decimal("15.99"),
            frequency=RecurrenceFrequency.MONTHLY,
            next_occurrence=date(2026, 9, 1),
        )
    ]

    save_recurring_expense_templates_to_file(
        templates,
        1,
        db_path,
    )

    assert db_path.exists()


def test_load_recurring_expense_templates_rejects_invalid_database_file(
    tmp_path,
):
    db_path = tmp_path / "recurring_expenses.db"
    db_path.write_text(
        "not a valid sqlite database",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Failed to load recurring expense templates",
    ):
        load_recurring_expense_templates_from_file(1, db_path)
