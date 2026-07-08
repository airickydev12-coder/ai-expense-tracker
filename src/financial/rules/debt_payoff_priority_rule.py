from src.financial.rules.base_rule import FinancialRule


class DebtPayoffPriorityRule(FinancialRule):
    """Recommend prioritizing the highest-interest active debt."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation for debt payoff priority."""
        debts = snapshot.get("debts", [])

        active_debts = [
            debt
            for debt in debts
            if debt["balance"] > 0
        ]

        if not active_debts:
            return None

        highest_interest_debt = max(
            active_debts,
            key=lambda debt: debt["interest_rate"],
        )

        if highest_interest_debt["interest_rate"] <= 0:
            return None

        return (
            f"Prioritize paying down {highest_interest_debt['name']} first "
            f"because it has the highest interest rate at "
            f"{highest_interest_debt['interest_rate']:.2f}%."
        )