from src.financial.rules.base_rule import FinancialRule


class HealthScoreRule(FinancialRule):
    """Evaluate financial health score."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation based on health score."""
        health_score = snapshot["health_score"]
        health_status = snapshot["health_status"]

        if health_score < 50:
            return (
                f"Your financial health status is {health_status}. "
                "Review your cash flow, debt, savings, and budget priorities."
            )

        if health_score >= 85:
            return (
                f"Your financial health status is {health_status}. "
                "Continue your current habits and consider long-term investing."
            )

        return None