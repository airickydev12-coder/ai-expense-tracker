from src.financial.rules.base_rule import FinancialRule


class DebtRatioRule(FinancialRule):
    """Warn when debt is high relative to available cash."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation for excessive debt."""

        total_debt = snapshot["total_debt"]
        account_balance = snapshot["total_account_balance"]

        if account_balance <= 0:
            if total_debt > 0:
                return (
                    "You have debt but no available cash reserves. "
                    "Prioritize building emergency savings."
                )
            return None

        ratio = total_debt / account_balance

        if ratio >= 1.0:
            return (
                "Your debt exceeds your available cash. "
                "Consider prioritizing debt repayment."
            )

        return None