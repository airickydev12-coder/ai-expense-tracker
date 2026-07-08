from src.financial.rules.base_rule import FinancialRule


class GoalCompletionRule(FinancialRule):
    """Recognize when a financial goal is complete."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation when a goal is complete."""
        goals = snapshot.get("goals", [])

        for goal in goals:
            if goal["target_amount"] <= 0:
                continue

            if goal["current_amount"] >= goal["target_amount"]:
                return (
                    f"Congratulations. Your goal '{goal['name']}' is fully funded. "
                    "Consider setting your next financial goal."
                )

        return None