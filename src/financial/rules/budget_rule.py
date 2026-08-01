from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule

BUDGET_UTILIZATION_CRITICAL_THRESHOLD = 0.90


class BudgetUtilizationRule(FinancialRule):
    """Warn when a budget is nearly exhausted."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation for high budget utilization."""
        for budget in snapshot.get("budget_report", []):
            limit = budget["limit"]
            spent = budget["spent"]

            if limit <= 0:
                continue

            utilization = spent / limit

            if utilization >= BUDGET_UTILIZATION_CRITICAL_THRESHOLD:
                return Recommendation(
                    priority=RecommendationPriority.HIGH,
                    category=RecommendationCategory.BUDGET,
                    title="Budget Nearly Exhausted",
                    message=(
                        f"Your {budget['category']} budget is "
                        f"{utilization:.0%} utilized."
                    ),
                    action="Review recent spending in this category.",
                )

        return None
