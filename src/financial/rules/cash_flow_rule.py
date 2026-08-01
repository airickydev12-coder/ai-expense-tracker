from src.financial.rules.base_rule import FinancialRule
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority


class NegativeCashFlowRule(FinancialRule):
    """Warn when expenses exceed income."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation if cash flow is negative."""
        if snapshot["net_cash_flow"] < 0:
            return Recommendation(
                priority=RecommendationPriority.CRITICAL,
                category=RecommendationCategory.CASH_FLOW,
                title="Negative Cash Flow",
                message="Your expenses exceed your income.",
                action="Reduce spending or increase income.",
            )

        return None
