from src.financial.rules.base_rule import FinancialRule


class RuleEngine:
    """Evaluates a collection of financial rules."""

    def __init__(self) -> None:
        self._rules: list[FinancialRule] = []

    def register(self, rule: FinancialRule) -> None:
        """Register a rule with the engine."""
        self._rules.append(rule)

    def evaluate(self, snapshot: dict) -> list[str]:
        """Evaluate all registered rules."""
        recommendations: list[str] = []

        for rule in self._rules:
            result = rule.evaluate(snapshot)
            if result is not None:
                recommendations.append(result)

        return recommendations