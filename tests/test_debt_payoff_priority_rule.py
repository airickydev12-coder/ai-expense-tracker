from src.financial.rules.debt_payoff_priority_rule import DebtPayoffPriorityRule


def test_debt_payoff_priority_rule_triggers():
    rule = DebtPayoffPriorityRule()

    snapshot = {
        "debts": [
            {
                "name": "Car Loan",
                "balance": 8000,
                "interest_rate": 6.5,
            },
            {
                "name": "Credit Card",
                "balance": 2500,
                "interest_rate": 24.99,
            },
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "Credit Card" in result


def test_debt_payoff_priority_rule_returns_none_without_debt():
    rule = DebtPayoffPriorityRule()

    snapshot = {
        "debts": []
    }

    result = rule.evaluate(snapshot)

    assert result is None


def test_debt_payoff_priority_rule_ignores_paid_off_debt():
    rule = DebtPayoffPriorityRule()

    snapshot = {
        "debts": [
            {
                "name": "Credit Card",
                "balance": 0,
                "interest_rate": 24.99,
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is None