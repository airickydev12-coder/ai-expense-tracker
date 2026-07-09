from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
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
    assert result.priority == RecommendationPriority.MEDIUM
    assert result.category == RecommendationCategory.EXPENSES
    assert result.title == "Expense Spike Detected"
    assert "Car Repair" in result.message


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