from src.financial.rules.base_rule import FinancialRule


class BudgetOverrunRule(FinancialRule):
    """Warn when a budget has been exceeded."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation if any budget is over limit."""
        for budget in snapshot.get("budget_report", []):
            remaining = budget["remaining"]

            if remaining < 0:
                return (
                    f"Your {budget['category']} budget is over by "
                    f"${abs(remaining):.2f}. Review recent spending."
                )

        return None