from datetime import date
from decimal import Decimal

import pytest

from src.financial.recurring_expenses.models import (
    RecurrenceFrequency,
    RecurringExpenseTemplate,
)
from src.financial.shared.categories import ExpenseCategory


def test_recurring_expense_template_creation():
    template = RecurringExpenseTemplate(
        id=1,
        name="Streaming Subscription",
        category=ExpenseCategory.ENTERTAINMENT,
        amount=Decimal("15.99"),
        frequency=RecurrenceFrequency.MONTHLY,
        next_occurrence=date(2026, 9, 1),
    )

    assert template.name == "Streaming Subscription"
    assert template.amount == Decimal("15.99")
    assert template.frequency == RecurrenceFrequency.MONTHLY
    assert template.next_occurrence == date(2026, 9, 1)
    assert template.is_active is True


def test_invalid_id():
    with pytest.raises(ValueError):
        RecurringExpenseTemplate(
            id=0,
            name="Streaming Subscription",
            category=ExpenseCategory.ENTERTAINMENT,
            amount=Decimal("15.99"),
            frequency=RecurrenceFrequency.MONTHLY,
            next_occurrence=date(2026, 9, 1),
        )


def test_empty_name():
    with pytest.raises(ValueError):
        RecurringExpenseTemplate(
            id=1,
            name="   ",
            category=ExpenseCategory.ENTERTAINMENT,
            amount=Decimal("15.99"),
            frequency=RecurrenceFrequency.MONTHLY,
            next_occurrence=date(2026, 9, 1),
        )


def test_negative_amount():
    with pytest.raises(ValueError):
        RecurringExpenseTemplate(
            id=1,
            name="Streaming Subscription",
            category=ExpenseCategory.ENTERTAINMENT,
            amount=Decimal("-15.99"),
            frequency=RecurrenceFrequency.MONTHLY,
            next_occurrence=date(2026, 9, 1),
        )


def test_to_dict_and_from_dict_round_trip():
    template = RecurringExpenseTemplate(
        id=1,
        name="Streaming Subscription",
        category=ExpenseCategory.ENTERTAINMENT,
        amount=Decimal("15.99"),
        frequency=RecurrenceFrequency.MONTHLY,
        next_occurrence=date(2026, 9, 1),
        is_active=False,
    )

    restored = RecurringExpenseTemplate.from_dict(template.to_dict())

    assert restored == template
