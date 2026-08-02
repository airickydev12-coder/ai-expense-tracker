from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.debt_to_income_rule import DebtToIncomeRule


def test_debt_to_income_rule_triggers():
    rule = DebtToIncomeRule()

    snapshot = {
        "total_income": 5000,
        "total_debt": 36000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.HIGH
    assert result.category == RecommendationCategory.DEBT
    assert result.title == "High Debt-to-Income Ratio"
    assert "60%" in result.message


def test_debt_to_income_rule_returns_none():
    rule = DebtToIncomeRule()

    snapshot = {
        "total_income": 5000,
        "total_debt": 1000,
    }

    result = rule.evaluate(snapshot)

    assert result is None


def test_debt_to_income_rule_handles_zero_income():
    rule = DebtToIncomeRule()

    snapshot = {
        "total_income": 0,
        "total_debt": 1000,
    }

    result = rule.evaluate(snapshot)

    assert result is None
