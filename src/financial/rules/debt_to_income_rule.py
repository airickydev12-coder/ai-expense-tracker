from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule

DEBT_TO_INCOME_HIGH_THRESHOLD = 0.50


class DebtToIncomeRule(FinancialRule):
    """Warn when debt is high compared to income."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation when debt-to-income is high."""
        total_income = snapshot["total_income"]
        total_debt = snapshot["total_debt"]

        if total_income <= 0:
            return None

        debt_to_income = total_debt / total_income

        if debt_to_income >= DEBT_TO_INCOME_HIGH_THRESHOLD:
            return Recommendation(
                priority=RecommendationPriority.HIGH,
                category=RecommendationCategory.DEBT,
                title="High Debt-to-Income Ratio",
                message=(f"Your debt is {debt_to_income:.0%} of your income."),
                action="Prioritize debt reduction to improve financial flexibility.",
            )

        return None
