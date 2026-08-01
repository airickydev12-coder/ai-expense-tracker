from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.debt_minimum_payment_rule import DebtMinimumPaymentRule


def test_debt_minimum_payment_rule_triggers():
    rule = DebtMinimumPaymentRule()

    snapshot = {
        "debts": [
            {
                "name": "Credit Card",
                "balance": 1000,
                "minimum_payment": 0,
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.MEDIUM
    assert result.category == RecommendationCategory.DEBT
    assert result.title == "Missing Minimum Payment"
    assert "Credit Card" in result.message


def test_debt_minimum_payment_rule_returns_none():
    rule = DebtMinimumPaymentRule()

    snapshot = {
        "debts": [
            {
                "name": "Credit Card",
                "balance": 1000,
                "minimum_payment": 50,
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is None
