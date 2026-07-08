from src.financial.rules.base_rule import FinancialRule


class FinancialIndependenceRule(FinancialRule):
    """Evaluate progress toward financial independence."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation based on financial independence progress."""
        net_worth = snapshot["net_worth"]
        monthly_expenses = snapshot["total_expenses"]

        if monthly_expenses <= 0:
            return None

        annual_expenses = monthly_expenses * 12
        target_net_worth = annual_expenses * 25  # 4% rule approximation

        progress = net_worth / target_net_worth

        if progress >= 1.0:
            return (
                "Congratulations! Based on the 4% guideline, you may have reached "
                "financial independence."
            )

        if progress >= 0.75:
            return (
                f"You are approximately {progress:.0%} of the way toward "
                "financial independence. Keep building assets."
            )

        return None