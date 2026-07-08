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
    assert "Credit Card" in result
    assert "high interest rate" in result


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