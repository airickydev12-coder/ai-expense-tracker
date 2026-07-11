from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class PositiveCashFlowAllocationRule(FinancialRule):
    """Recommend how to use positive cash flow."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation when positive cash flow exists."""
        net_cash_flow = snapshot["net_cash_flow"]
        total_debt = snapshot["total_debt"]
        total_goal_progress = snapshot["total_goal_progress"]

        if net_cash_flow <= 0:
            return None

        if total_debt > 0:
            return Recommendation(
                priority=RecommendationPriority.HIGH,
                category=RecommendationCategory.CASH_FLOW,
                title="Apply Cash Flow to Debt",
                message=(
                    f"You have ${net_cash_flow:.2f} in positive cash flow "
                    "and outstanding debt."
                ),
                action="Apply a portion of your positive cash flow to debt repayment.",
            )

        if total_goal_progress <= 0:
            return Recommendation(
                priority=RecommendationPriority.MEDIUM,
                category=RecommendationCategory.GOALS,
                title="Fund a Financial Goal",
                message=(
                    f"You have ${net_cash_flow:.2f} in positive cash flow "
                    "and no recorded goal progress."
                ),
                action="Direct part of your positive cash flow toward a financial goal.",
            )

        return Recommendation(
            priority=RecommendationPriority.LOW,
            category=RecommendationCategory.WEALTH,
            title="Allocate Excess Cash Flow",
            message=f"You have ${net_cash_flow:.2f} in positive cash flow.",
            action="Consider saving, investing, or increasing goal contributions.",
        )