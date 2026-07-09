from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class IncomeCoverageRule(FinancialRule):
    """Evaluate whether income covers expenses."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation when income does not cover expenses."""
        income = snapshot["total_income"]
        expenses = snapshot["total_expenses"]

        if expenses <= 0:
            return None

        coverage_ratio = income / expenses

        if coverage_ratio < 1:
            return Recommendation(
                priority=RecommendationPriority.CRITICAL,
                category=RecommendationCategory.INCOME,
                title="Income Does Not Cover Expenses",
                message="Your income does not fully cover your expenses.",
                action="Review spending, income sources, or budget priorities.",
            )

        return None