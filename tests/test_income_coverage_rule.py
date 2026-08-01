from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.income_coverage_rule import IncomeCoverageRule


def test_income_coverage_rule_triggers():
    rule = IncomeCoverageRule()

    snapshot = {
        "total_income": 1500,
        "total_expenses": 2000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.CRITICAL
    assert result.category == RecommendationCategory.INCOME
    assert result.title == "Income Does Not Cover Expenses"


def test_income_coverage_rule_returns_none():
    rule = IncomeCoverageRule()

    snapshot = {
        "total_income": 3000,
        "total_expenses": 2000,
    }

    result = rule.evaluate(snapshot)

    assert result is None
