from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule

EXPENSE_SPIKE_MULTIPLIER = 3


class ExpenseSpikeRule(FinancialRule):
    """Warn when the largest expense is much higher than average."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation when an expense spike is detected."""
        largest_expense = snapshot.get("largest_expense")
        average_expense = snapshot.get("average_expense")

        if largest_expense is None or average_expense is None:
            return None

        if average_expense <= 0:
            return None

        if largest_expense["amount"] >= average_expense * EXPENSE_SPIKE_MULTIPLIER:
            return Recommendation(
                priority=RecommendationPriority.MEDIUM,
                category=RecommendationCategory.EXPENSES,
                title="Expense Spike Detected",
                message=(
                    f"{largest_expense['name']} is significantly higher "
                    "than your average expense."
                ),
                action="Review whether this expense was expected.",
            )

        return None
