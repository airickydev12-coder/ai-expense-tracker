from src.financial.rules.base_rule import FinancialRule


class NetWorthRule(FinancialRule):
    """Evaluate net worth health."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation if net worth is negative."""
        net_worth = snapshot["net_worth"]

        if net_worth < 0:
            return (
                "Your net worth is negative. Focus on reducing debt, "
                "building savings, and increasing assets."
            )

        return None