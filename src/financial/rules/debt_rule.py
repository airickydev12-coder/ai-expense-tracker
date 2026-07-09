from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class DebtRatioRule(FinancialRule):
    """Warn when debt is high relative to assets."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation if debt ratio is too high."""
        assets = (
            snapshot["total_account_balance"]
            + snapshot["total_goal_progress"]
        )

        if assets <= 0:
            return None

        ratio = snapshot["total_debt"] / assets

        if ratio >= 0.50:
            return Recommendation(
                priority=RecommendationPriority.HIGH,
                category=RecommendationCategory.DEBT,
                title="High Debt Ratio",
                message=(
                    f"Your debt equals {ratio:.0%} of your tracked assets."
                ),
                action=(
                    "Focus on reducing debt while continuing to build assets."
                ),
            )

        return None