from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class FinancialIndependenceRule(FinancialRule):
    """Evaluate progress toward financial independence."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation based on financial independence progress."""
        net_worth = snapshot["net_worth"]
        monthly_expenses = snapshot["total_expenses"]

        if monthly_expenses <= 0:
            return None

        annual_expenses = monthly_expenses * 12
        target_net_worth = annual_expenses * 25
        progress = net_worth / target_net_worth

        if progress >= 1.0:
            return Recommendation(
                priority=RecommendationPriority.LOW,
                category=RecommendationCategory.WEALTH,
                title="Financial Independence Reached",
                message=(
                    "Based on the 4% guideline, your net worth may support "
                    "your current level of spending."
                ),
                action=(
                    "Review your assumptions and consider speaking with a "
                    "qualified financial professional before making major decisions."
                ),
            )

        if progress >= 0.75:
            return Recommendation(
                priority=RecommendationPriority.MEDIUM,
                category=RecommendationCategory.WEALTH,
                title="Approaching Financial Independence",
                message=(
                    f"You are approximately {progress:.0%} of the way toward "
                    "your estimated financial independence target."
                ),
                action="Continue building assets and controlling long-term expenses.",
            )

        return None