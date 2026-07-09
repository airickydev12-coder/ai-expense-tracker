from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class ZeroIncomeRule(FinancialRule):
    """Warn when no income has been recorded."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation when income is zero."""
        income = snapshot["total_income"]
        expenses = snapshot["total_expenses"]

        if income <= 0 and expenses > 0:
            return Recommendation(
                priority=RecommendationPriority.CRITICAL,
                category=RecommendationCategory.INCOME,
                title="No Income Recorded",
                message="No income has been recorded while expenses exist.",
                action="Add income sources so Financial Core can calculate accurate cash flow.",
            )

        return None