from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class NetWorthRule(FinancialRule):
    """Evaluate net worth health."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation if net worth is negative."""
        net_worth = snapshot["net_worth"]

        if net_worth < 0:
            return Recommendation(
                priority=RecommendationPriority.CRITICAL,
                category=RecommendationCategory.WEALTH,
                title="Negative Net Worth",
                message="Your net worth is negative.",
                action="Focus on reducing debt, building savings, and increasing assets.",
            )

        return None