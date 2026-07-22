from decimal import Decimal

from src.financial.income.models import Income


def get_total_income(income_entries: list[Income]) -> Decimal:
    """Calculate total income."""
    return sum(
        (income.amount for income in income_entries),
        Decimal("0"),
    )


def get_average_income(income_entries: list[Income]) -> Decimal:
    """Calculate average income."""
    if not income_entries:
        return Decimal("0")

    return get_total_income(income_entries) / Decimal(len(income_entries))


def get_highest_income(
    income_entries: list[Income],
) -> Income | None:
    """Find the highest income entry."""
    if not income_entries:
        return None

    return max(
        income_entries,
        key=lambda income: income.amount,
    )
