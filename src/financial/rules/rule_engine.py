from src.financial.rules.base_rule import FinancialRule
from src.financial.rules.budget_overrun_rule import BudgetOverrunRule
from src.financial.rules.budget_rule import BudgetUtilizationRule
from src.financial.rules.cash_flow_rule import NegativeCashFlowRule
from src.financial.rules.debt_minimum_payment_rule import DebtMinimumPaymentRule
from src.financial.rules.debt_payoff_priority_rule import DebtPayoffPriorityRule
from src.financial.rules.debt_rule import DebtRatioRule
from src.financial.rules.debt_to_income_rule import DebtToIncomeRule
from src.financial.rules.emergency_fund_rule import EmergencyFundRule
from src.financial.rules.expense_spike_rule import ExpenseSpikeRule
from src.financial.rules.goal_completion_rule import GoalCompletionRule
from src.financial.rules.goal_progress_rule import GoalProgressRule
from src.financial.rules.goal_progress_threshold_rule import GoalProgressThresholdRule
from src.financial.rules.health_score_rule import HealthScoreRule
from src.financial.rules.high_interest_debt_rule import HighInterestDebtRule
from src.financial.rules.income_coverage_rule import IncomeCoverageRule
from src.financial.rules.low_account_balance_rule import LowAccountBalanceRule
from src.financial.rules.net_worth_rule import NetWorthRule
from src.financial.rules.positive_cash_flow_rule import PositiveCashFlowAllocationRule
from src.financial.recommendations.models import Recommendation
from src.financial.rules.savings_rate_rule import SavingsRateRule
from src.financial.rules.spending_concentration_rule import SpendingConcentrationRule
from src.financial.rules.zero_income_rule import ZeroIncomeRule
from src.financial.rules.bill_due_rule import BillDueSoonRule


class RuleEngine:
    """Evaluates a collection of financial rules."""

    def __init__(self) -> None:
        self._rules: list[FinancialRule] = []

    def register(self, rule: FinancialRule) -> None:
        """Register a rule with the engine."""
        self._rules.append(rule)

    def evaluate(self, snapshot: dict) -> list[Recommendation]:
        """Evaluate all registered rules."""
        recommendations: list[Recommendation] = []

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
    engine.register(BillDueSoonRule())
    engine.register(NetWorthRule())
    engine.register(HealthScoreRule())
    engine.register(BudgetOverrunRule())
    engine.register(DebtMinimumPaymentRule())
    engine.register(HighInterestDebtRule())
    engine.register(LowAccountBalanceRule())
    engine.register(GoalCompletionRule())
    engine.register(GoalProgressThresholdRule())
    engine.register(IncomeCoverageRule())
    engine.register(ExpenseSpikeRule())
    engine.register(ZeroIncomeRule())
    engine.register(SpendingConcentrationRule())
    engine.register(DebtToIncomeRule())
    engine.register(PositiveCashFlowAllocationRule())
    engine.register(DebtPayoffPriorityRule())

    return engine
