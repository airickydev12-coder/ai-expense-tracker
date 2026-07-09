from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.net_worth_rule import NetWorthRule


def test_net_worth_rule_triggers():
    rule = NetWorthRule()

    snapshot = {
        "net_worth": -1000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.CRITICAL
    assert result.category == RecommendationCategory.WEALTH
    assert result.title == "Negative Net Worth"


def test_net_worth_rule_returns_none():
    rule = NetWorthRule()

    snapshot = {
        "net_worth": 1000,
    }

    result = rule.evaluate(snapshot)

    assert result is None