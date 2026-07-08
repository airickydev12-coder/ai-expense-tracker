from src.financial.rules.base_rule import FinancialRule


class ExpenseSpikeRule(FinancialRule):
    """Warn when the largest expense is much higher than average."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation when an expense spike is detected."""
        largest_expense = snapshot.get("largest_expense")
        average_expense = snapshot.get("average_expense")

        if largest_expense is None or average_expense is None:
            return None

        if average_expense <= 0:
            return None

        if largest_expense["amount"] >= average_expense * 3:
            return (
                f"{largest_expense['name']} is significantly higher than your "
                "average expense. Review whether this was expected."
            )

        return None