from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class GoalCompletionRule(FinancialRule):
    """Recognize when a financial goal is complete."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation when a goal is complete."""
        goals = snapshot.get("goals", [])

        for goal in goals:
            if goal["target_amount"] <= 0:
                continue

            if goal["current_amount"] >= goal["target_amount"]:
                return Recommendation(
                    priority=RecommendationPriority.LOW,
                    category=RecommendationCategory.GOALS,
                    title="Goal Completed",
                    message=f"Your goal '{goal['name']}' is fully funded.",
                    action="Consider setting your next financial goal.",
                )

        return None