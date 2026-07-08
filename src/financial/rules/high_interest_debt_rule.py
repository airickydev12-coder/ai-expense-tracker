from src.financial.rules.base_rule import FinancialRule


class HighInterestDebtRule(FinancialRule):
    """Warn when debt has a high interest rate."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation if high-interest debt exists."""
        debts = snapshot.get("debts", [])

        for debt in debts:
            if debt["balance"] > 0 and debt["interest_rate"] >= 15:
                return (
                    f"{debt['name']} has a high interest rate "
                    f"of {debt['interest_rate']:.2f}%. "
                    "Consider prioritizing this debt for repayment."
                )

        return None