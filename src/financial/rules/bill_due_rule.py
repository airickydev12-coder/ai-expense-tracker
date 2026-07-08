from src.financial.rules.base_rule import FinancialRule


class BillDueSoonRule(FinancialRule):
    """Warn when bills are due soon."""

    def evaluate(self, snapshot: dict) -> str | None:
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
                return (
                    f"{bill['name']} is due in {days_until_due} days. "
                    "Make sure funds are available."
                )

        return None