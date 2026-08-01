from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class DebtPayoffPriorityRule(FinancialRule):
    """Recommend prioritizing the highest-interest active debt."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation for debt payoff priority."""
        debts = snapshot.get("debts", [])

        active_debts = [debt for debt in debts if debt["balance"] > 0]

        if not active_debts:
            return None

        highest_interest_debt = max(
            active_debts,
            key=lambda debt: debt["interest_rate"],
        )

        if highest_interest_debt["interest_rate"] <= 0:
            return None

        return Recommendation(
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.DEBT,
            title="Debt Payoff Priority",
            message=(
                f"{highest_interest_debt['name']} has the highest interest "
                f"rate at {highest_interest_debt['interest_rate']:.2f}%."
            ),
            action="Prioritize this debt first to reduce interest costs.",
        )
