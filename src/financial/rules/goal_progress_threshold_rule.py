from src.financial.rules.base_rule import FinancialRule


class GoalProgressThresholdRule(FinancialRule):
    """Warn when a financial goal has low progress."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation when goal progress is low."""
        goals = snapshot.get("goals", [])

        for goal in goals:
            target_amount = goal["target_amount"]
            current_amount = goal["current_amount"]

            if target_amount <= 0:
                continue

            progress = current_amount / target_amount

            if progress < 0.25:
                return (
                    f"Your goal '{goal['name']}' is less than 25% funded. "
                    "Consider increasing contributions."
                )

        return None