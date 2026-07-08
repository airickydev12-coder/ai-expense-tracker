from src.financial.rules.base_rule import FinancialRule
from src.financial.rules.recommendation import Recommendation


class NegativeCashFlowRule(FinancialRule):
    """Warn when expenses exceed income."""

    def evaluate(self, snapshot: dict) -> Recommendation | None:
        """Return a recommendation if cash flow is negative."""
        if snapshot["net_cash_flow"] < 0:
            return Recommendation(
                priority="Critical",
                category="Cash Flow",
                title="Negative Cash Flow",
                message="Your expenses exceed your income.",
                action="Reduce spending or increase income.",
            )

        return None