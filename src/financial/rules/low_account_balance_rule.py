from src.financial.rules.base_rule import FinancialRule


class LowAccountBalanceRule(FinancialRule):
    """Warn when account balance is low compared to expenses."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation if cash balance is low."""
        account_balance = snapshot["total_account_balance"]
        expenses = snapshot["total_expenses"]

        if expenses <= 0:
            return None

        if account_balance < expenses:
            return (
                "Your available cash is less than one month of expenses. "
                "Consider building cash reserves."
            )

        return None