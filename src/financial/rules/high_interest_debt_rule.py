from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class HighInterestDebtRule(FinancialRule):
    """Warn when debt has a high interest rate."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation if high-interest debt exists."""
        debts = snapshot.get("debts", [])

        for debt in debts:
            if debt["balance"] > 0 and debt["interest_rate"] >= 15:
                return Recommendation(
                    priority=RecommendationPriority.HIGH,
                    category=RecommendationCategory.DEBT,
                    title="High Interest Debt",
                    message=(
                        f"{debt['name']} has a high interest rate "
                        f"of {debt['interest_rate']:.2f}%."
                    ),
                    action="Prioritize this debt for repayment.",
                )

        return None