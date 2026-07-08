from src.financial.rules.base_rule import FinancialRule


class DebtMinimumPaymentRule(FinancialRule):
    """Warn when a debt has no minimum payment configured."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation if debt minimum payments are missing."""
        debts = snapshot.get("debts", [])

        for debt in debts:
            if debt["balance"] > 0 and debt["minimum_payment"] <= 0:
                return (
                    f"{debt['name']} has a balance but no minimum payment. "
                    "Add a minimum payment to improve debt planning."
                )

        return None