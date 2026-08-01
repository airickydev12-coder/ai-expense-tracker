from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule

SAVINGS_RATE_LOW_THRESHOLD = 0.10
SAVINGS_RATE_STRONG_THRESHOLD = 0.20


class SavingsRateRule(FinancialRule):
    """Evaluate the user's monthly savings rate."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation based on savings rate."""
        income = snapshot["total_income"]

        if income <= 0:
            return None

        savings_rate = snapshot["net_cash_flow"] / income

        if savings_rate < SAVINGS_RATE_LOW_THRESHOLD:
            return Recommendation(
                priority=RecommendationPriority.HIGH,
                category=RecommendationCategory.SAVINGS,
                title="Low Savings Rate",
                message="Your savings rate is below 10%.",
                action="Aim to save at least 10% of your income.",
            )

        if savings_rate >= SAVINGS_RATE_STRONG_THRESHOLD:
            return Recommendation(
                priority=RecommendationPriority.LOW,
                category=RecommendationCategory.SAVINGS,
                title="Strong Savings Rate",
                message="Your savings rate is excellent.",
                action="Consider investing excess cash to build long-term wealth.",
            )

        return None
