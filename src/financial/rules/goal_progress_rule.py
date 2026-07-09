from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class GoalProgressRule(FinancialRule):
    """Evaluate whether goal progress is present."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation based on goal progress."""
        goal_progress = snapshot["total_goal_progress"]

        if goal_progress <= 0:
            return Recommendation(
                priority=RecommendationPriority.MEDIUM,
                category=RecommendationCategory.GOALS,
                title="No Goal Progress",
                message="You have not made progress toward your financial goals yet.",
                action="Consider contributing a portion of your cash flow to a goal.",
            )

        return None