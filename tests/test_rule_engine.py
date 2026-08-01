from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.cash_flow_rule import NegativeCashFlowRule
from src.financial.rules.rule_engine import RuleEngine


def test_rule_engine_returns_recommendations():
    engine = RuleEngine()
    engine.register(NegativeCashFlowRule())

    snapshot = {
        "net_cash_flow": -100,
    }

    results = engine.evaluate(snapshot)

    assert len(results) == 1
    assert results[0].title == "Negative Cash Flow"
    assert results[0].category == RecommendationCategory.CASH_FLOW
    assert results[0].priority == RecommendationPriority.CRITICAL


def test_rule_engine_returns_empty_list():
    engine = RuleEngine()
    engine.register(NegativeCashFlowRule())

    snapshot = {
        "net_cash_flow": 100,
    }

    results = engine.evaluate(snapshot)

    assert results == []
