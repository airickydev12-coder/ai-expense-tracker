from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.financial_independence_rule import (
    FinancialIndependenceRule,
)


def test_financial_independence_complete():
    rule = FinancialIndependenceRule()

    snapshot = {
        "net_worth": 900000,
        "total_expenses": 3000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.LOW
    assert result.category == RecommendationCategory.WEALTH
    assert result.title == "Financial Independence Reached"


def test_financial_independence_progress():
    rule = FinancialIndependenceRule()

    snapshot = {
        "net_worth": 700000,
        "total_expenses": 3000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.MEDIUM
    assert result.category == RecommendationCategory.WEALTH
    assert result.title == "Approaching Financial Independence"


def test_financial_independence_returns_none():
    rule = FinancialIndependenceRule()

    snapshot = {
        "net_worth": 100000,
        "total_expenses": 3000,
    }

    result = rule.evaluate(snapshot)

    assert result is None