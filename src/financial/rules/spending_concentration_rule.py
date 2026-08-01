from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule

SPENDING_CONCENTRATION_HIGH_THRESHOLD = 0.50


class SpendingConcentrationRule(FinancialRule):
    """Detect excessive spending concentration in one category."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation when one category dominates spending."""
        category_totals = snapshot.get("category_totals", {})

        if not category_totals:
            return None

        total_spending = sum(category_totals.values())

        if total_spending <= 0:
            return None

        largest_category = max(category_totals, key=category_totals.get)
        largest_amount = category_totals[largest_category]
        concentration = largest_amount / total_spending

        if concentration >= SPENDING_CONCENTRATION_HIGH_THRESHOLD:
            return Recommendation(
                priority=RecommendationPriority.MEDIUM,
                category=RecommendationCategory.EXPENSES,
                title="Spending Concentration Detected",
                message=(
                    f"{largest_category} represents "
                    f"{concentration:.0%} of your spending."
                ),
                action="Review this category for possible optimization.",
            )

        return None
