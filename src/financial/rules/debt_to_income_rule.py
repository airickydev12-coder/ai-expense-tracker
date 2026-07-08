from src.financial.rules.base_rule import FinancialRule


class DebtToIncomeRule(FinancialRule):
    """Warn when debt is high compared to income."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation when debt-to-income is high."""
        total_income = snapshot["total_income"]
        total_debt = snapshot["total_debt"]

        if total_income <= 0:
            return None

        debt_to_income = total_debt / total_income

        if debt_to_income >= 0.50:
            return (
                f"Your debt is {debt_to_income:.0%} of your income. "
                "Consider prioritizing debt reduction."
            )

        return None