from src.financial.rules.base_rule import FinancialRule


class ZeroIncomeRule(FinancialRule):
    """Warn when no income has been recorded."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation when income is zero."""
        income = snapshot["total_income"]
        expenses = snapshot["total_expenses"]

        if income <= 0 and expenses > 0:
            return (
                "No income has been recorded while expenses exist. "
                "Add income sources so Financial Core can calculate accurate cash flow."
            )

        return None