from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class LowAccountBalanceRule(FinancialRule):
    """Warn when account balance is low compared to expenses."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation if cash balance is low."""
        account_balance = snapshot["total_account_balance"]
        expenses = snapshot["total_expenses"]

        if expenses <= 0:
            return None

        if account_balance < expenses:
            return Recommendation(
                priority=RecommendationPriority.HIGH,
                category=RecommendationCategory.SAVINGS,
                title="Low Cash Reserves",
                message="Your available cash is less than one month of expenses.",
                action="Build cash reserves to cover at least one month of expenses.",
            )

        return None
