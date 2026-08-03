"""Tests for CSV export of recorded expenses."""

import csv
import io
from decimal import Decimal

from src.financial.expenses.export import export_expenses_to_csv
from src.financial.expenses.models import Expense
from src.financial.shared.categories import ExpenseCategory


def test_export_expenses_to_csv_includes_header_and_rows():
    expenses = [
        Expense(id=1, name="Groceries", category=ExpenseCategory.FOOD, amount=Decimal("100.00")),
        Expense(
            id=2,
            name="Gas",
            category=ExpenseCategory.TRANSPORTATION,
            amount=Decimal("50.00"),
        ),
    ]

    csv_text = export_expenses_to_csv(expenses)
    rows = list(csv.reader(io.StringIO(csv_text)))

    assert rows[0] == ["id", "name", "category", "amount"]
    assert rows[1] == ["1", "Groceries", "Food", "100.00"]
    assert rows[2] == ["2", "Gas", "Transportation", "50.00"]
    assert len(rows) == 3


def test_export_expenses_to_csv_handles_empty_list():
    csv_text = export_expenses_to_csv([])
    rows = list(csv.reader(io.StringIO(csv_text)))

    assert rows == [["id", "name", "category", "amount"]]
