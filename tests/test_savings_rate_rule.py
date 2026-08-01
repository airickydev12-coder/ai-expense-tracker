from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.savings_rate_rule import SavingsRateRule


def test_low_savings_rate():
    rule = SavingsRateRule()

    snapshot = {
        "total_income": 5000,
        "net_cash_flow": 250,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.HIGH
    assert result.category == RecommendationCategory.SAVINGS
    assert result.title == "Low Savings Rate"


def test_high_savings_rate():
    rule = SavingsRateRule()

    snapshot = {
        "total_income": 5000,
        "net_cash_flow": 1500,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.LOW
    assert result.category == RecommendationCategory.SAVINGS
    assert result.title == "Strong Savings Rate"


def test_average_savings_rate():
    rule = SavingsRateRule()

    snapshot = {
        "total_income": 5000,
        "net_cash_flow": 750,
    }

    result = rule.evaluate(snapshot)

    assert result is None


def test_zero_income():
    rule = SavingsRateRule()

    snapshot = {
        "total_income": 0,
        "net_cash_flow": 0,
    }

    assert rule.evaluate(snapshot) is None
