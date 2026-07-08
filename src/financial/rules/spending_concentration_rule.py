from src.financial.rules.base_rule import FinancialRule


class SpendingConcentrationRule(FinancialRule):
    """Detect excessive spending concentration in one category."""

    def evaluate(self, snapshot: dict) -> str | None:
        """Return a recommendation when one category dominates spending."""
        category_totals = snapshot.get("category_totals", {})

        if not category_totals:
            return None

        total_spending = sum(category_totals.values())

        if total_spending <= 0:
            return None

        largest_category = max(category_totals, key=category_totals.get)
        largest_amount = category_totals[largest_category]

        concentration = largest_amount / total_spending

        if concentration >= 0.50:
            return (
                f"{largest_category} represents "
                f"{concentration:.0%} of your spending. "
                "Review this category for possible optimization."
            )

        return None