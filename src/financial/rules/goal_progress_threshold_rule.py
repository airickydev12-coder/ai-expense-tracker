from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class GoalProgressThresholdRule(FinancialRule):
    """Warn when a financial goal has low progress."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation when goal progress is low."""
        goals = snapshot.get("goals", [])

        for goal in goals:
            target_amount = goal["target_amount"]
            current_amount = goal["current_amount"]

            if target_amount <= 0:
                continue

            progress = current_amount / target_amount

            if progress < 0.25:
                return Recommendation(
                    priority=RecommendationPriority.MEDIUM,
                    category=RecommendationCategory.GOALS,
                    title="Low Goal Progress",
                    message=(
                        f"Your goal '{goal['name']}' is "
                        f"{progress:.0%} funded."
                    ),
                    action="Consider increasing contributions toward this goal.",
                )

        return None