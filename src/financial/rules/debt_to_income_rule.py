from src.core.constants import MONTHS_PER_YEAR
from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule

DEBT_TO_INCOME_HIGH_THRESHOLD = 0.50


class DebtToIncomeRule(FinancialRule):
    """Warn when debt is high compared to annualized income."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation when debt-to-income is high."""
        monthly_income = snapshot["total_income"]
        total_debt = snapshot["total_debt"]

        if monthly_income <= 0:
            return None

        annual_income = monthly_income * MONTHS_PER_YEAR

        debt_to_income = total_debt / annual_income

        if debt_to_income >= DEBT_TO_INCOME_HIGH_THRESHOLD:
            return Recommendation(
                priority=RecommendationPriority.HIGH,
                category=RecommendationCategory.DEBT,
                title="High Debt-to-Income Ratio",
                message=(f"Your debt is {debt_to_income:.0%} of your income."),
                action="Prioritize debt reduction to improve financial flexibility.",
            )

        return None
