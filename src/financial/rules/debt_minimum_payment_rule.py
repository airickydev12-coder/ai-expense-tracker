from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class DebtMinimumPaymentRule(FinancialRule):
    """Warn when a debt has no minimum payment configured."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation if debt minimum payments are missing."""
        debts = snapshot.get("debts", [])

        for debt in debts:
            if debt["balance"] > 0 and debt["minimum_payment"] <= 0:
                return Recommendation(
                    priority=RecommendationPriority.MEDIUM,
                    category=RecommendationCategory.DEBT,
                    title="Missing Minimum Payment",
                    message=(
                        f"{debt['name']} has a balance but no minimum "
                        "payment configured."
                    ),
                    action="Add a minimum payment to improve debt planning.",
                )

        return None
