from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.high_interest_debt_rule import HighInterestDebtRule


def test_high_interest_debt_rule_triggers():
    rule = HighInterestDebtRule()

    snapshot = {
        "debts": [
            {
                "name": "Credit Card",
                "balance": 1000,
                "interest_rate": 24.99,
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.HIGH
    assert result.category == RecommendationCategory.DEBT
    assert result.title == "High Interest Debt"
    assert "Credit Card" in result.message


def test_high_interest_debt_rule_returns_none():
    rule = HighInterestDebtRule()

    snapshot = {
        "debts": [
            {
                "name": "Car Loan",
                "balance": 8000,
                "interest_rate": 6.5,
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is None
