from src.financial.rules.base_rule import FinancialRule


class PositiveCashFlowAllocationRule(FinancialRule):
    """Recommend allocation when cash flow is positive."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation when positive cash flow exists."""
        net_cash_flow = snapshot["net_cash_flow"]
        total_debt = snapshot["total_debt"]
        total_goal_progress = snapshot["total_goal_progress"]

        if net_cash_flow <= 0:
            return None

        if total_debt > 0:
            return (
                "You have positive cash flow. Consider applying a portion "
                "toward debt repayment."
            )

        if total_goal_progress <= 0:
            return (
                "You have positive cash flow. Consider directing part of it "
                "toward your financial goals."
            )

        return (
            "You have positive cash flow. Consider saving, investing, "
            "or increasing goal contributions."
        )