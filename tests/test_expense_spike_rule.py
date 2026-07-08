from src.financial.rules.expense_spike_rule import ExpenseSpikeRule


def test_expense_spike_rule_triggers():
    rule = ExpenseSpikeRule()

    snapshot = {
        "largest_expense": {
            "name": "Car Repair",
            "amount": 900,
        },
        "average_expense": 200,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "Car Repair" in result


def test_expense_spike_rule_returns_none():
    rule = ExpenseSpikeRule()

    snapshot = {
        "largest_expense": {
            "name": "Groceries",
            "amount": 250,
        },
        "average_expense": 200,
    }

    result = rule.evaluate(snapshot)

    assert result is None