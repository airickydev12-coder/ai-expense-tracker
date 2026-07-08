from src.financial.rules.base_rule import FinancialRule


class SavingsRateRule(FinancialRule):
    """Evaluate the user's monthly savings rate."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation based on savings rate."""
        income = snapshot["total_income"]

        if income <= 0:
            return None

        savings_rate = snapshot["net_cash_flow"] / income

        if savings_rate < 0.10:
            return (
                "Your savings rate is below 10%. "
                "Aim to save at least 10% of your income."
            )

        if savings_rate >= 0.20:
            return (
                "Excellent savings rate. "
                "Consider investing excess cash to build long-term wealth."
            )

        return None