from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.base_rule import FinancialRule


class BillDueSoonRule(FinancialRule):
    """Warn when bills are due soon."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation if unpaid bills are due soon."""
        bills = snapshot.get("bills", [])
        current_day = snapshot.get("current_day")

        if current_day is None:
            return None

        for bill in bills:
            if bill["is_paid"]:
                continue

            days_until_due = bill["due_day"] - current_day

            if 0 <= days_until_due <= 7:
                return Recommendation(
                    priority=RecommendationPriority.HIGH,
                    category=RecommendationCategory.BILLS,
                    title="Bill Due Soon",
                    message=f"{bill['name']} is due in {days_until_due} days.",
                    action="Make sure funds are available before the due date.",
                )

        return None