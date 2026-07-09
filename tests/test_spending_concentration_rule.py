from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.spending_concentration_rule import (
    SpendingConcentrationRule,
)


def test_spending_concentration_rule_triggers():
    rule = SpendingConcentrationRule()

    snapshot = {
        "category_totals": {
            "Housing": 2500,
            "Food": 300,
            "Transportation": 200,
        }
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.MEDIUM
    assert result.category == RecommendationCategory.EXPENSES
    assert result.title == "Spending Concentration Detected"
    assert "Housing" in result.message


def test_spending_concentration_rule_returns_none():
    rule = SpendingConcentrationRule()

    snapshot = {
        "category_totals": {
            "Housing": 1000,
            "Food": 900,
            "Transportation": 800,
        }
    }

    result = rule.evaluate(snapshot)

    assert result is None