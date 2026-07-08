from src.financial.rules.base_rule import FinancialRule


class GoalProgressRule(FinancialRule):
    """Evaluate whether goal progress is present."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation based on goal progress."""
        goal_progress = snapshot["total_goal_progress"]

        if goal_progress <= 0:
            return (
                "You have not made progress toward your financial goals yet. "
                "Consider contributing a portion of your cash flow to a goal."
            )

        return None