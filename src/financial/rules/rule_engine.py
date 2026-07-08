from src.financial.rules.base_rule import FinancialRule
from src.financial.rules.budget_rule import BudgetUtilizationRule
from src.financial.rules.cash_flow_rule import NegativeCashFlowRule
from src.financial.rules.debt_rule import DebtRatioRule
from src.financial.rules.emergency_fund_rule import EmergencyFundRule
from src.financial.rules.savings_rate_rule import SavingsRateRule
from src.financial.rules.goal_progress_rule import GoalProgressRule

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


def create_default_rule_engine() -> RuleEngine:
    """Create a rule engine with the standard financial rules."""
    engine = RuleEngine()

    engine.register(NegativeCashFlowRule())
    engine.register(BudgetUtilizationRule())
    engine.register(DebtRatioRule())
    engine.register(EmergencyFundRule())
    engine.register(SavingsRateRule())
    engine.register(GoalProgressRule())

    return engine