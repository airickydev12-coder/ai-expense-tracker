from src.financial.income.models import Income


def get_total_income(income_entries: list[Income]) -> float:
    """Calculate total income."""
    return sum(income.amount for income in income_entries)


def get_average_income(income_entries: list[Income]) -> float:
    """Calculate average income."""
    if not income_entries:
        return 0.0

    return get_total_income(income_entries) / len(income_entries)


def get_highest_income(income_entries: list[Income]) -> Income | None:
    """Find the highest income entry."""
    if not income_entries:
        return None

    return max(income_entries, key=lambda income: income.amount)