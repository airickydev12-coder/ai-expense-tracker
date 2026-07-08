from src.financial.rules.base_rule import FinancialRule


class IncomeCoverageRule(FinancialRule):
    """Evaluate whether income covers expenses."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation when income does not cover expenses."""
        income = snapshot["total_income"]
        expenses = snapshot["total_expenses"]

        if expenses <= 0:
            return None

        coverage_ratio = income / expenses

        if coverage_ratio < 1:
            return (
                "Your income does not fully cover your expenses. "
                "Review spending, income sources, or budget priorities."
            )

        return None