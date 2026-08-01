from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule

EMERGENCY_FUND_MONTHS_THRESHOLD = 3


class EmergencyFundRule(FinancialRule):
    """Warn when available cash reserves are low."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation if emergency savings are too low."""
        monthly_expenses = snapshot["total_expenses"]
        account_balance = snapshot["total_account_balance"]

        if monthly_expenses <= 0:
            return None

        months_covered = account_balance / monthly_expenses

        if months_covered < EMERGENCY_FUND_MONTHS_THRESHOLD:
            return Recommendation(
                priority=RecommendationPriority.HIGH,
                category=RecommendationCategory.SAVINGS,
                title="Low Emergency Fund",
                message=(
                    f"Your emergency fund covers approximately "
                    f"{months_covered:.1f} months of expenses."
                ),
                action=(
                    "Build cash reserves until you cover at least 3 months of expenses."
                ),
            )

        return None
