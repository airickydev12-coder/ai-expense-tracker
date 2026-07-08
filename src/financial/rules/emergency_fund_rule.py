from src.financial.rules.base_rule import FinancialRule


class EmergencyFundRule(FinancialRule):
    """Warn when available cash reserves are low."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation if emergency savings are too low."""
        monthly_expenses = snapshot["total_expenses"]
        account_balance = snapshot["total_account_balance"]

        if monthly_expenses <= 0:
            return None

        months_covered = account_balance / monthly_expenses

        if months_covered < 3:
            return (
                "Your emergency fund covers less than 3 months of expenses. "
                "Consider building your cash reserves."
            )

        return None