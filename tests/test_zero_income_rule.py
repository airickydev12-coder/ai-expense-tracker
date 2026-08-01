from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.zero_income_rule import ZeroIncomeRule


def test_zero_income_rule_triggers():
    rule = ZeroIncomeRule()

    snapshot = {
        "total_income": 0,
        "total_expenses": 1500,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.CRITICAL
    assert result.category == RecommendationCategory.INCOME
    assert result.title == "No Income Recorded"


def test_zero_income_rule_returns_none_when_income_exists():
    rule = ZeroIncomeRule()

    snapshot = {
        "total_income": 5000,
        "total_expenses": 1500,
    }

    result = rule.evaluate(snapshot)

    assert result is None


def test_zero_income_rule_returns_none_when_no_expenses():
    rule = ZeroIncomeRule()

    snapshot = {
        "total_income": 0,
        "total_expenses": 0,
    }

    result = rule.evaluate(snapshot)

    assert result is None
