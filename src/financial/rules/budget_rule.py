from src.financial.rules.base_rule import FinancialRule
from src.financial.recommendations.models import Recommendation


class BudgetUtilizationRule(FinancialRule):
    """Warn when a budget is nearly exhausted."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation for high budget utilization."""
        for budget in snapshot.get("budget_report", []):
            limit = budget["limit"]
            spent = budget["spent"]

            if limit <= 0:
                continue

            utilization = spent / limit

            if utilization >= 0.90:
                return Recommendation(
                    priority="High",
                    category="Budget",
                    title="Budget Nearly Exhausted",
                    message=(
                        f"Your {budget['category']} budget is "
                        f"{utilization:.0%} utilized."
                    ),
                    action="Review recent spending in this category.",
                )

        return None
