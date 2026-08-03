"""CSV export for recorded expenses."""

import csv
import io

from src.financial.expenses.models import Expense

CSV_HEADER = ["id", "name", "category", "amount"]


def export_expenses_to_csv(expenses: list[Expense]) -> str:
    """Return recorded expenses serialized as CSV text."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(CSV_HEADER)
    for expense in expenses:
        writer.writerow(
            [
                expense.id,
                expense.name,
                expense.category.value,
                str(expense.amount),
            ]
        )

    return buffer.getvalue()
