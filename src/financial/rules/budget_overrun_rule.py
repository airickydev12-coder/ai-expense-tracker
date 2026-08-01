from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class BudgetOverrunRule(FinancialRule):
    """Warn when a budget has been exceeded."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation if any budget is over limit."""
        for budget in snapshot.get("budget_report", []):
            remaining = budget["remaining"]

            if remaining < 0:
                return Recommendation(
                    priority=RecommendationPriority.CRITICAL,
                    category=RecommendationCategory.BUDGET,
                    title="Budget Overrun",
                    message=(
                        f"Your {budget['category']} budget is over by "
                        f"${abs(remaining):.2f}."
                    ),
                    action=(
                        "Review recent spending and reduce expenses in this category."
                    ),
                )

        return None
