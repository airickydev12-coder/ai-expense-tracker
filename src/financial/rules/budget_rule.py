from src.financial.rules.base_rule import FinancialRule


class BudgetUtilizationRule(FinancialRule):
    """Warn when a budget is nearly exhausted."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation for high budget utilization."""
        for budget in snapshot.get("budget_report", []):
            limit = budget["limit"]
            spent = budget["spent"]

            if limit <= 0:
                continue

            utilization = spent / limit

            if utilization >= 0.90:
                return (
                    f"Your {budget['category']} budget is "
                    f"{utilization:.0%} utilized."
                )

        return None