from src.financial.rules.base_rule import FinancialRule


class NegativeCashFlowRule(FinancialRule):
    """Warn when expenses exceed income."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation if cash flow is negative."""
        if snapshot["net_cash_flow"] < 0:
            return "Your expenses exceed your income. Reduce spending or increase income."

        return None