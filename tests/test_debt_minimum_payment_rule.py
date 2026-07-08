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
    assert "Credit Card" in result


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